"""
Konfigurasi scheduler untuk otomatisasi broadcast WhatsApp
Diatur untuk berjalan setiap tanggal 5
"""
import asyncio
import logging
from datetime import datetime, date
import os

from ..database import get_db
from ..schedulers.whatsapp_scheduler import WhatsAppScheduler
from ..services.broadcast_service import BroadcastService
from ..services.qontak_service import QontakService
from ..services.qontak_service import (
    WhatsAppService,
    QontakLanguage,
    QontakParameters,
    QontakBody,
    QontakButton
)

logger = logging.getLogger(__name__)

class SchedulerConfig:
    """Konfigurasi scheduler untuk otomatisasi broadcast"""

    def __init__(self):
        # Cek apakah scheduler diaktifkan
        self.enabled = os.getenv("WHATSAPP_SCHEDULER_ENABLED", "true").lower() == "true"

        # Tanggal untuk pengiriman otomatis (default: tanggal 5)
        self.target_day = int(os.getenv("WHATSAPP_TARGET_DAY", "5"))

        # Jam pengiriman (default: 09:00)
        self.target_hour = int(os.getenv("WHATSAPP_TARGET_HOUR", "9"))
        self.target_minute = int(os.getenv("WHATSAPP_TARGET_MINUTE", "0"))

        # Database session untuk async operations
        self.db_session = None

    async def initialize(self):
        """Inisialisasi scheduler dan services"""
        if not self.enabled:
            logger.info("WhatsApp scheduler dinonaktifkan")
            return

        logger.info("Menginisialisasi WhatsApp scheduler...")

        # Inisialisasi services
        self.scheduler = WhatsAppScheduler()
        self.broadcast_service = BroadcastService()
        self.qontak_service = QontakService()

        # Dapatkan database session
        self.db_session = get_db()

        logger.info("WhatsApp scheduler berhasil diinisialisasi")

    async def check_and_run_reminder(self):
        """Cek tanggal dan jalankan pengiriman reminder jika tanggal 5"""
        today = date.today()

        if today.day != self.target_day:
            logger.info(f"Hari ini bukan tanggal {self.target_day}, skip pengiriman reminder")
            return

        # Cek waktu untuk pengiriman
        now = datetime.now()

        if now.hour < self.target_hour:
            logger.info(f"Waktu pengiriman belum tiba (sekarang: {now.hour}, target: {self.target_hour})")
            return

        if now.hour == self.target_hour and now.minute < self.target_minute:
            logger.info(f"Menit pengiriman belum tiba (sekarang: {now.minute}, target: {self.target_minute})")
            return

        logger.info("Memulai pengiriman reminder otomatis...")

        try:
            async for db in self.db_session:
                # Cek apakah sudah pernah mengirim reminder hari ini
                await self.send_monthly_reminder(db)
                break  # Hanya jalankan sekali per hari

        except Exception as e:
            logger.error(f"Gagal menjalankan pengiriman reminder otomatis: {e}")

    async def send_monthly_reminder(self, db):
        """Kirim reminder bulanan ke semua pelanggan"""
        logger.info("Memulai pengiriman reminder bulanan...")

        try:
            # Get all active customers for reminder
            from ..models.langganan import Langganan
            from ..models.user import User

            query = (
                select(Langganan, User)
                .join(User)
                .where(Langganan.status == Langganan.STATUS_AKTIF)
                .options(selectinload(Langganan.user))
            )

            result = await db.execute(query)
            customers = result.all()

            if not customers:
                logger.info("Tidak ada pelanggan aktif untuk dikirim reminder")
                return

            logger.info(f"Menemukan {len(customers)} pelanggan aktif")

            success_count = 0
            error_count = 0

            for langganan, user in customers:
                try:
                    # Format nomor telepon untuk WhatsApp
                    phone_number = self.format_phone_number(user.no_telp or langganan.user.no_telp)

                    if not phone_number:
                        logger.warning(f"Nomor telepon tidak valid untuk pelanggan {user.nama}")
                        error_count += 1
                        continue

                    # Generate personalized message
                    message = self.generate_reminder_message(user.nama, langganan.paket_layanan.nama)

                    # Kirim via Qontak API
                    success = await self.send_whatsapp_message(
                        phone_number=phone_number,
                        message=message
                    )

                    if success:
                        success_count += 1
                        logger.info(f"Reminder berhasil dikirim ke {user.nama}")
                    else:
                        error_count += 1
                        logger.error(f"Gagal mengirim reminder ke {user.nama}")

                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing customer {user.nama}: {e}")

            logger.info(f"Pengiriman reminder selesai. Sukses: {success_count}, Error: {error_count}")

        except Exception as e:
            logger.error(f"Error in send_monthly_reminder: {e}")

    def format_phone_number(self, phone: str) -> str:
        """Format nomor telepon untuk WhatsApp API"""
        if not phone:
            return ""

        # Hapus karakter non-numeric
        phone = ''.join(filter(str.isdigit, phone))

        # Jika dimulai dengan 0, ganti dengan 62
        if phone.startswith('0'):
            phone = '62' + phone[1:]

        # Validasi panjang minimal
        if len(phone) >= 10:  # Minimal 10 digit
            return phone

        return ""

    def generate_reminder_message(self, customer_name: str, package_name: str) -> str:
        """Generate pesan reminder yang dipersonalisasi"""
        message = f"""Halo {customer_name},

Ini adalah reminder otomatis dari sistem Billing Jelantik.

Paket layanan Anda: *{package_name}*

Silakan lakukan pembayaran sebelum tanggal jatuh tempo untuk menghindari penonaktifan layanan.

Terima kasih atas perhatian Anda.

* Billing Jelantik *

---
Pesan ini dikirim otomatis pada tanggal {date.today().strftime('%d %B %Y')}.
        """

        return message.strip()

    async def send_whatsapp_message(self, phone_number: str, message: str) -> bool:
        """Kirim pesan WhatsApp via Qontak API"""
        try:
            # Initialize Qontak service
            qontak_service = QontakService()

            # Send message
            result = await qontak_service.send_whatsapp_message(
                phone_number=phone_number,
                message=message
            )

            return result.get("success", False)

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    async def run_scheduler(self):
        """Run scheduler untuk cek dan kirim reminder"""
        try:
            await self.initialize()
            await self.check_and_run_reminder()
        except Exception as e:
            logger.error(f"Error running scheduler: {e}")
        finally:
            if self.db_session:
                await self.db_session.close()

# Function untuk dipanggil dari script atau API
async def run_whatsapp_reminder():
    """Main function untuk menjalankan reminder otomatis"""
    config = SchedulerConfig()
    await config.run_scheduler()

if __name__ == "__main__":
    # Run scheduler jika script ini dijalankan langsung
    asyncio.run(run_whatsapp_reminder())