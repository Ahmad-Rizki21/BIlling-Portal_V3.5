"""
Scheduler untuk otomatisasi broadcast WhatsApp ke pelanggan
Sesuai dengan kebutuhan untuk pengiriman reminder tanggal 5 setiap bulan
"""
import asyncio
import logging
from datetime import datetime, date
from typing import Optional
import os

from ..database import get_db
from ..services.whatsapp_service import WhatsAppService
from ..services.broadcast_service import BroadcastService
from ..models.pelanggan import Pelanggan

logger = logging.getLogger(__name__)

class WhatsAppScheduler:
    """Scheduler untuk otomatisasi broadcast WhatsApp"""

    def __init__(self):
        self.whatsapp_service = WhatsAppService()
        self.broadcast_service = BroadcastService()

    async def send_monthly_reminder(self, test_mode: bool = False) -> dict:
        """
        Kirim reminder setiap tanggal 5 kepada pelanggan
        Sesuai dengan kebutuhan pengguna
        """
        logger.info("Memulai pengiriman reminder bulanan...")

        # Cek apakah hari ini tanggal 5 (kecuali test mode)
        if not test_mode:
            today = date.today()
            if today.day != 5:
                logger.info(f"Hari ini bukan tanggal 5 (hari ini: {today.day}), skip pengiriman reminder")
                return {
                    "success": True,
                    "message": f"Hari ini bukan tanggal 5, pengiriman reminder di-skip",
                    "sent_count": 0,
                    "total_count": 0
                }

        # Ambil semua pelanggan aktif
        async for db in get_db():
            try:
                # Query untuk mendapatkan semua pelanggan aktif
                stmt = select(Pelanggan).where(Pelanggan.is_active == True)
                result = await db.execute(stmt)
                pelanggan_list = result.scalars().all()

                if not pelanggan_list:
                    logger.info("Tidak ada pelanggan aktif yang ditemukan")
                    return {
                        "success": True,
                        "message": "Tidak ada pelanggan aktif",
                        "sent_count": 0,
                        "total_count": 0
                    }

                total_count = len(pelanggan_list)
                sent_count = 0
                failed_count = 0
                errors = []

                logger.info(f"Menemukan {total_count} pelanggan aktif, akan mengirim reminder...")

                # Kirim reminder ke setiap pelanggan
                for pelanggan in pelanggan_list:
                    try:
                        if pelanggan.no_telp:  # Cek apakah pelanggan memiliki nomor telepon
                            await self.whatsapp_service.send_reminder(
                                to_number=pelanggan.no_telp,
                                to_name=pelanggan.nama or f"Pelanggan #{pelanggan.id}",
                                test_mode=test_mode
                            )
                            sent_count += 1
                            logger.info(f"Reminder berhasil dikirim ke {pelanggan.nama} ({pelanggan.no_telp})")
                        else:
                            logger.warning(f"Pelanggan {pelanggan.nama} tidak memiliki nomor telepon, skip")
                            failed_count += 1
                            errors.append(f"Pelanggan {pelanggan.nama} tidak memiliki nomor telepon")

                    except Exception as e:
                        logger.error(f"Gagal mengirim reminder ke {pelanggan.nama}: {str(e)}")
                        failed_count += 1
                        errors.append(f"Gagal ke {pelanggan.nama}: {str(e)}")

                result = {
                    "success": True,
                    "message": f"Pengiriman reminder selesai. Berhasil: {sent_count}, Gagal: {failed_count}",
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "total_count": total_count,
                    "errors": errors[:10] if errors else []  # Batasi error yang ditampilkan
                }

                logger.info(f"Pengiriman reminder selesai: {result}")
                return result

            except Exception as e:
                logger.error(f"Error dalam pengiriman reminder: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "sent_count": 0,
                    "failed_count": 0,
                    "total_count": 0,
                    "errors": [str(e)]
                }

    async def check_and_send_reminder(self) -> dict:
        """
        Cek dan kirim reminder jika hari ini tanggal 5
        Method ini bisa dipanggil oleh scheduler otomatis
        """
        logger.info("Menjalankan pengecekan reminder otomatis...")

        # Cek apakah hari ini tanggal 5
        today = date.today()
        if today.day == 5:
            logger.info("Hari ini tanggal 5, akan mengirim reminder bulanan...")
            return await self.send_monthly_reminder(test_mode=False)
        else:
            logger.info(f"Hari ini bukan tanggal 5 (hari ini: {today.day}), skip pengiriman reminder")
            return {
                "success": True,
                "message": f"Hari ini bukan tanggal 5, reminder tidak dikirim",
                "sent_count": 0,
                "total_count": 0
            }

    async def send_custom_message_to_all(
        self,
        message_type: str,
        custom_message: Optional[str] = None
    ) -> dict:
        """
        Kirim pesan custom ke semua pelanggan aktif
        Message types:
        - 'reminder': Reminder bulanan (tanggal 5)
        - 'promotion': Pesan promosi
        - 'custom': Pesan custom
        """
        logger.info(f"Memulai pengiriman pesan {message_type} ke semua pelanggan...")

        async for db in get_db():
            try:
                # Query untuk mendapatkan semua pelanggan aktif
                stmt = select(Pelanggan).where(Pelanggan.is_active == True)
                result = await db.execute(stmt)
                pelanggan_list = result.scalars().all()

                if not pelanggan_list:
                    logger.info("Tidak ada pelanggan aktif yang ditemukan")
                    return {
                        "success": True,
                        "message": "Tidak ada pelanggan aktif",
                        "sent_count": 0,
                        "total_count": 0
                    }

                total_count = len(pelanggan_list)
                sent_count = 0
                failed_count = 0
                errors = []

                logger.info(f"Menemukan {total_count} pelanggan aktif, akan mengirim pesan {message_type}...")

                # Kirim pesan ke setiap pelanggan
                for pelanggan in pelanggan_list:
                    try:
                        if pelanggan.no_telp:  # Cek apakah pelanggan memiliki nomor telepon
                            if message_type == 'reminder':
                                await self.whatsapp_service.send_reminder(
                                    to_number=pelanggan.no_telp,
                                    to_name=pelanggan.nama or f"Pelanggan #{pelanggan.id}",
                                    test_mode=True  # Mode test untuk pengiriman manual
                                )
                            elif message_type == 'promotion':
                                await self.whatsapp_service.send_promotion(
                                    to_number=pelanggan.no_telp,
                                    to_name=pelanggan.nama or f"Pelanggan #{pelanggan.id}",
                                    test_mode=True
                                )
                            elif message_type == 'custom' and custom_message:
                                await self.whatsapp_service.send_custom_message(
                                    to_number=pelanggan.no_telp,
                                    to_name=pelanggan.nama or f"Pelanggan #{pelanggan.id}",
                                    message=custom_message,
                                    test_mode=True
                                )
                            else:
                                logger.warning(f"Message type '{message_type}' tidak valid, skip")
                                failed_count += 1
                                continue

                            sent_count += 1
                            logger.info(f"Pesan {message_type} berhasil dikirim ke {pelanggan.nama} ({pelanggan.no_telp})")
                        else:
                            logger.warning(f"Pelanggan {pelanggan.nama} tidak memiliki nomor telepon, skip")
                            failed_count += 1
                            errors.append(f"Pelanggan {pelanggan.nama} tidak memiliki nomor telepon")

                    except Exception as e:
                        logger.error(f"Gagal mengirim pesan {message_type} ke {pelanggan.nama}: {str(e)}")
                        failed_count += 1
                        errors.append(f"Gagal ke {pelanggan.nama}: {str(e)}")

                result = {
                    "success": True,
                    "message": f"Pengiriman pesan {message_type} selesai. Berhasil: {sent_count}, Gagal: {failed_count}",
                    "sent_count": sent_count,
                    "failed_count": failed_count,
                    "total_count": total_count,
                    "errors": errors[:10] if errors else []  # Batasi error yang ditampilkan
                }

                logger.info(f"Pengiriman pesan {message_type} selesai: {result}")
                return result

            except Exception as e:
                logger.error(f"Error dalam pengiriman pesan {message_type}: {str(e)}")
                return {
                    "success": False,
                    "message": f"Error: {str(e)}",
                    "sent_count": 0,
                    "failed_count": 0,
                    "total_count": 0,
                    "errors": [str(e)]
                }

# Singleton instance
scheduler = WhatsAppScheduler()

async def run_scheduler_test():
    """
    Test function untuk menjalankan scheduler
    """
    print("Testing WhatsApp scheduler...")

    # Test pengiriman reminder
    print("\n1. Testing pengiriman reminder...")
    result = await scheduler.send_monthly_reminder(test_mode=True)
    print(f"Result: {result}")

    # Test pengiriman custom message
    print("\n2. Testing pengiriman custom message...")
    result = await scheduler.send_custom_message_to_all(
        message_type='custom',
        custom_message='Ini adalah pesan test dari sistem'
    )
    print(f"Result: {result}")

if __name__ == "__main__":
    # Jalankan test jika file ini dijalankan langsung
    asyncio.run(run_scheduler_test())