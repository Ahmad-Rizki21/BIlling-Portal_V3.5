# app/jobs.py
"""
Modul ini berisi semua background job dan scheduler yang jalan otomatis.
Fungsinya buat ngurusin rutinitas billing system yang harus jalan tiap hari/hari.
Misalnya bikin invoice, suspend pelanggan, cek pembayaran, dll.
Ini penting banget buat sistem yang jalan 24/7 tanpa perlu campur tangan admin.
"""

import logging
import math
import traceback
import uuid
import calendar
import time
from datetime import date, datetime, timedelta
from sqlalchemy import Date as SQLDate

from dateutil.relativedelta import relativedelta
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.engine import Result
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

# Impor komponen
from .database import AsyncSessionLocal
from .database import get_db
from .websocket_manager import manager

# Type hints untuk Pylance
SessionType: async_sessionmaker[AsyncSession] = AsyncSessionLocal  # type: ignore
from .logging_config import log_scheduler_event
from .models import DataTeknis as DataTeknisModel
from .models import Invoice as InvoiceModel
from .models import Langganan as LanggananModel
from .models import Pelanggan as PelangganModel
from .routers.invoice import _process_successful_payment
from .services import mikrotik_service, xendit_service
from .services.rate_limiter import create_invoice_with_rate_limit, InvoicePriority

logger = logging.getLogger("app.jobs")


import re

# ... (rest of the imports)

async def generate_single_invoice(db: AsyncSession, langganan: LanggananModel) -> None:
    # ... (try block starts)
    try:
        pelanggan = langganan.pelanggan
        paket = langganan.paket_layanan
        brand = pelanggan.harga_layanan
        data_teknis = pelanggan.data_teknis

        if not all([pelanggan, paket, brand, data_teknis]):
            logger.error(f"Data tidak lengkap untuk langganan ID {langganan.id}. Skip.")
            return

        harga_dasar = float(paket.harga)
        pajak_persen = float(brand.pajak)
        pajak_mentah = harga_dasar * (pajak_persen / 100)
        pajak = math.floor(pajak_mentah + 0.5)
        total_harga = harga_dasar + pajak

        # --- MODIFICATION FOR INVOICE NUMBER ---
        # 1. Sanitize and prepare customer name and address
        import calendar
        nama_pelanggan_singkat = re.sub(r'[^a-zA-Z0-9]', '', pelanggan.nama).upper()
        alamat_singkat = re.sub(r'[^a-zA-Z0-9]', '', pelanggan.alamat or '').upper()
        brand_singkat = re.sub(r'[^a-zA-Z0-9]', '', brand.brand or '').upper()

        # 2. Format untuk bulan-tahun
        bulan_tahun = f"{calendar.month_name[date.today().month].upper()}-{date.today().year}"

        # 3. Generate new invoice number (sama format dengan manual)
        nomor_invoice_baru = f"{brand_singkat}/ftth/{nama_pelanggan_singkat}/{bulan_tahun}/{alamat_singkat}/{str(data_teknis.id_pelanggan)[-3:]}"

        # 4. Check for duplicate invoice number and add timestamp if needed
        existing_invoice_number = (await db.execute(
            select(InvoiceModel.id).where(InvoiceModel.invoice_number == nomor_invoice_baru)
        )).scalar_one_or_none()

        if existing_invoice_number:
            # Generate nomor unik dengan tambahan timestamp atau random
            import time
            timestamp = str(int(time.time()))[-6:]  # 6 digit terakhir timestamp
            nomor_invoice_baru = f"{nomor_invoice_baru}/{timestamp}"
        # --- END OF MODIFICATION ---

        new_invoice_data = {
            "invoice_number": nomor_invoice_baru, # Use the new invoice number
            "pelanggan_id": pelanggan.id,
            "id_pelanggan": data_teknis.id_pelanggan,
            "brand": brand.brand,
            "total_harga": total_harga,
            "no_telp": pelanggan.no_telp,
            "email": pelanggan.email,
            "tgl_invoice": date.today(),
            "tgl_jatuh_tempo": langganan.tgl_jatuh_tempo,
            "status_invoice": "Belum Dibayar",
        }

        db_invoice = InvoiceModel(**new_invoice_data)
        # ... (rest of the function)

        deskripsi_xendit = ""
        jatuh_tempo_str_lengkap = datetime.combine(date.fromisoformat(str(db_invoice.tgl_jatuh_tempo)), datetime.min.time()).strftime("%d/%m/%Y")

        if langganan.metode_pembayaran == "Prorate":
            

            # Hitung harga normal untuk perbandingan
            harga_normal_full = float(paket.harga) * (1 + (float(brand.pajak) / 100))

            # Cek apakah ini invoice gabungan
            if db_invoice.total_harga > (harga_normal_full + 1):
                # INI TAGIHAN GABUNGAN
                invoice_date = date.fromisoformat(str(db_invoice.tgl_invoice))
                jatuh_tempo_date = date.fromisoformat(str(db_invoice.tgl_jatuh_tempo))

                start_day = invoice_date.day
                end_day = jatuh_tempo_date.day
                periode_prorate_str = datetime.combine(jatuh_tempo_date, datetime.min.time()).strftime("%B %Y")
                periode_berikutnya_str = datetime.combine(jatuh_tempo_date + relativedelta(months=1), datetime.min.time()).strftime("%B %Y")

                deskripsi_xendit = (
                    f"Biaya internet up to {paket.kecepatan} Mbps. "
                    f"Periode Prorate {start_day}-{end_day} {periode_prorate_str} + "
                    f"Periode {periode_berikutnya_str}"
                )
            else:
                # INI TAGIHAN PRORATE BIASA
                invoice_date = date.fromisoformat(str(db_invoice.tgl_invoice))
                jatuh_tempo_date = date.fromisoformat(str(db_invoice.tgl_jatuh_tempo))

                start_day = invoice_date.day
                end_day = jatuh_tempo_date.day
                periode_str = datetime.combine(jatuh_tempo_date, datetime.min.time()).strftime("%B %Y")
                deskripsi_xendit = (
                    f"Biaya berlangganan internet up to {paket.kecepatan} Mbps, "
                    f"Periode Tgl {start_day}-{end_day} {periode_str}"
                )

        else:  # Otomatis
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps "
                f"jatuh tempo pembayaran tanggal {jatuh_tempo_str_lengkap}"
            )

        no_telp_xendit = f"+62{pelanggan.no_telp.lstrip('0')}" if pelanggan.no_telp else ""

        # Determine priority for rate limiting
        priority = InvoicePriority.NORMAL
        if hasattr(pelanggan, 'is_vip') and getattr(pelanggan, 'is_vip', False):
            priority = InvoicePriority.HIGH
        elif hasattr(pelanggan, 'tipe') and getattr(pelanggan, 'tipe', '') == 'bulk':
            priority = InvoicePriority.LOW

        xendit_response = await create_invoice_with_rate_limit(
            invoice=db_invoice,
            pelanggan=pelanggan,
            paket=paket,
            deskripsi_xendit=deskripsi_xendit,
            pajak=pajak,
            no_telp_xendit=no_telp_xendit,
            priority=priority
        )

        # VALIDASI RESPONSE dari Xendit
        if not xendit_response or not xendit_response.get("id"):
            raise ValueError(f"Invalid Xendit response: {xendit_response}")

        db_invoice.payment_link = xendit_response.get("short_url", xendit_response.get("invoice_url"))
        db_invoice.xendit_id = xendit_response.get("id")
        db_invoice.xendit_external_id = xendit_response.get("external_id")

        db.add(db_invoice)
        logger.info(f"✅ Invoice {db_invoice.invoice_number} BERHASIL dengan payment link dan WhatsApp notification")
        logger.info(f"📱 WhatsApp notification sent to: {pelanggan.nama} ({pelanggan.no_telp})")

    except Exception as e:
        # 🔧 FIX: Save invoice even if Xendit fails, but log for manual retry
        logger.error(f"⚠️ Xendit API gagal untuk Langganan ID {langganan.id}: {e}")
        logger.error(f"📝 Invoice {new_invoice_data.get('invoice_number', 'UNKNOWN')} akan disimpan tanpa payment link untuk retry otomatis")

        # Save invoice tanpa payment link untuk retry otomatis nanti
        try:
            # Tambah field retry tracking
            new_invoice_data.update({
                'xendit_status': 'failed',
                'xendit_error_message': str(e),
                'xendit_retry_count': 0,
            })

            db_invoice = InvoiceModel(**new_invoice_data)
            db.add(db_invoice)
            logger.info(f"🔄 Invoice {db_invoice.invoice_number} disimpan tanpa payment link (akan di-retry otomatis)")
        except Exception as db_error:
            logger.error(f"❌ Database error juga: {db_error}")
        # Re-raise biar scheduler tau ada issue


# ==========================================================
# --- JOB SCHEDULER YANG SUDAH DIOPTIMALKAN ---
# ==========================================================


async def job_generate_invoices() -> None:
    """
    Job scheduler yang jalan tiap hari buat bikin invoice otomatis.
    Scheduler ini bakal jalan setiap jam 00:00 (sesuai konfigurasi).

    LOGIKA BISNIS YANG BENAR:
    - H-5 sebelum jatuh tempo: Generate invoice & payment link
    - Contoh: Jatuh tempo 1 Des, maka tanggal 26 Nov generate payment link
    - Contoh: Jatuh tempo 1 Jan, maka tanggal 27 Des generate payment link

    Logic yang dijalanin:
    1. Cari semua langganan aktif yang jatuh tempo 5 hari lagi (H-5)
    2. Proses secara bertahap (batching) biar nggak berat server
    3. Buat invoice buat tiap pelanggan yang belum ada invoice-nya
    4. Generate payment link via Xendit
    5. Log hasil proses buat monitoring

    Performance optimization:
    - Batch processing (100 records per batch)
    - Eager loading relasi buat minimize database queries
    - Single query buat cek existing invoice

    Returns:
        None (hasilnya langsung di-log)

    Integration:
    - Xendit API buat payment gateway
    - Database invoice generation
    - Logger buat monitoring
    """
    log_scheduler_event(logger, "job_generate_invoices", "started")
    target_due_date = date.today() + timedelta(days=5)
    total_invoices_created = 0
    BATCH_SIZE = 100
    offset = 0

    logger.info(f"🔍 Mencari langganan yang jatuh tempo pada: {target_due_date.strftime('%d %B %Y')} (H-5)")

    async with SessionType() as db:
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .where(
                        LanggananModel.tgl_jatuh_tempo == target_due_date,
                        LanggananModel.status == "Aktif",
                    )
                    .options(
                        selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                        selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis),
                        selectinload(LanggananModel.paket_layanan),
                    )
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                subscriptions_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not subscriptions_batch:
                    break

                # OPTIMISASI: Ambil semua invoice yang sudah ada untuk batch ini dalam satu query
                pelanggan_ids_in_batch = [s.pelanggan_id for s in subscriptions_batch]

                # FIX: Check duplicate berdasarkan PERIODE BULAN, bukan exact date
                # Calculate month period for target_due_date
                target_year = target_due_date.year
                target_month = target_due_date.month
                start_of_month = date(target_year, target_month, 1)
                if target_month == 12:
                    end_of_month = date(target_year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_of_month = date(target_year, target_month + 1, 1) - timedelta(days=1)

                existing_invoices_stmt = select(InvoiceModel.pelanggan_id).where(
                    InvoiceModel.pelanggan_id.in_(pelanggan_ids_in_batch),
                    InvoiceModel.tgl_jatuh_tempo.between(start_of_month, end_of_month),
                )
                existing_invoices_pelanggan_ids = {row[0] for row in await db.execute(existing_invoices_stmt)}

                for langganan in subscriptions_batch:
                    # Cek dari data yang sudah di-prefetch, bukan query baru
                    if langganan.pelanggan_id not in existing_invoices_pelanggan_ids:
                        await generate_single_invoice(db, langganan)
                        total_invoices_created += 1

                await db.commit()
                offset += BATCH_SIZE

            except Exception as e:
                await db.rollback()
                error_details = traceback.format_exc()
                logger.error(f"[FAIL] Scheduler 'job_generate_invoices' failed at offset {offset}. Details:\n{error_details}")
                break

    if total_invoices_created > 0:
        log_scheduler_event(
            logger,
            "job_generate_invoices",
            "completed",
            f"Berhasil membuat {total_invoices_created} invoice baru.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_generate_invoices",
            "completed",
            "Tidak ada invoice baru yang perlu dibuat.",
        )


async def job_suspend_services() -> None:
    """
    Job scheduler buat suspend pelanggan yang telat bayar.
    Jalan setiap tanggal 5 untuk cek siapa aja yang udah overdue.

    LOGIKA BISNIS YANG BENAR:
    - H-5 (tgl 26): Generate payment link untuk jatuh tempo tgl 1 bulan depan
    - Tgl 1-4: Grace period untuk pembayaran
    - Tgl 5 jam 00:00 WIB: Otomatis suspend user yang belum bayar
    - Contoh: Jatuh tempo 1 Des, tgl 5 Des jam 00:00 suspend

    Logic suspend:
    1. Cari pelanggan yang jatuh tempo tanggal 1 bulan ini dan belum bayar
    2. Tepat tanggal 5 jam 00:00 WIB, suspend layanan mereka
    3. Ubah status langganan jadi 'Suspended'
    4. Ubah semua invoice belum bayar jadi 'Kadaluarsa'
    5. Trigger update ke Mikrotik buat blokir internet (disabled PPPoE secret)
    6. Log hasil proses

    Aturan suspend (LOGIKA BISNIS):
    - Jatuh tempo: 1 Desember 2025
    - Payment link generated: 26 November 2025 (H-5)
    - Grace period: 1-4 Desember (4 hari)
    - Suspend: 5 Desember jam 00:00 WIB
    - Enable kembali: Setelah bayar, re-activate service

    NOTE: Berdasarkan fungsi create_langganan, sebagian besar pelanggan dengan
    metode pembayaran "Otomatis" akan memiliki tgl_jatuh_tempo tanggal 1 setiap bulan,
    jadi job ini memang fokus ke tanggal 1 setiap bulan.

    Integration:
    - Mikrotik API buat suspend/blokir internet (PPPoE secret disabled)
    - Database status updates
    - Audit logging

    Performance:
    - Batch processing (50 records per batch)
    - Transaction rollback kalau ada error
    """
    log_scheduler_event(logger, "job_suspend_services", "started")
    total_services_suspended = 0
    total_invoices_overdue = 0
    current_date = date.today()
    BATCH_SIZE = 50
    offset = 0

    # LOGIKA BISNIS YANG BENAR:
    # Cek apakah hari ini adalah tanggal 5 untuk melakukan suspend utama
    is_main_suspend_day = current_date.day == 5

    # Tambahkan retroactive mechanism untuk tanggal 6-10 (jika scheduler gagal tanggal 5)
    is_retroactive_day = 6 <= current_date.day <= 10

    if not (is_main_suspend_day or is_retroactive_day):
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            f"Hari ini tanggal {current_date.day}, suspend hanya dilakukan tanggal 5-10 (retroactive). Sesuai logika bisnis: H-5 generate payment link, tanggal 5 auto suspend.",
        )
        return

    suspend_type = "RETROACTIVE" if is_retroactive_day else "SCHEDULED"
    if is_retroactive_day:
        logger.warning(f"🔄 RETROACTIVE SUSPEND: Menjalankan suspend ketinggalan dari tanggal 5 untuk hari {current_date.day}")
    else:
        logger.info(f"⏰ SCHEDULED SUSPEND: Menjalankan suspend otomatis tanggal 5 jam 00:00 WIB")

    # Target tanggal jatuh tempo yang harus disuspend sesuai logika bisnis:
    # Contoh: Invoice terbit H-5 sebelum tanggal jatuh tempo
    # Jika jatuh tempo 1 Desember, maka invoice terbit 26 November (H-5)
    # Tepat tanggal 5 Desember jam 00:00, semua invoice yang masih "Belum Dibayar" dan jatuh tempo akan disuspend
    #
    # Maka logika: Hari ini tanggal 5 Desember -> cari semua invoice yang jatuh tempo tanggal 1 Desember
    # dan statusnya masih "Belum Dibayar"

    # Tapi lebih umumnya: Jika hari ini tanggal 5 bulan ini, cari invoice yang jatuh tempo tanggal 1 bulan ini
    current_month = current_date.month
    current_year = current_date.year

    # Target tanggal jatuh tempo yang sesuai dengan logika bisnis
    target_due_date = date(current_year, current_month, 1)

    logger.info(f"🔍 Mencari pelanggan yang jatuh tempo tanggal {target_due_date.strftime('%d %B %Y')} dan belum bayar (Payment link generated H-5)")

    async with SessionType() as db:
        while True:
            try:
                # Filter tambahan untuk retroactive: hindari yang sudah disuspend
                if is_retroactive_day:
                    logger.info(f"🔍 Retroactive mode: mencari pelanggan yang belum disuspend dari tanggal 5")
                    base_stmt = (
                        select(LanggananModel)
                        .join(
                            InvoiceModel,
                            LanggananModel.pelanggan_id == InvoiceModel.pelanggan_id,
                        )
                        .where(
                            InvoiceModel.tgl_jatuh_tempo == target_due_date,  # Cari yang jatuh tempo tepat tanggal 1
                            LanggananModel.status == "Aktif",  # Masih aktif (belum suspend)
                            InvoiceModel.status_invoice == "Belum Dibayar",  # Invoice belum lunas
                        )
                        .distinct(LanggananModel.id)  # Pastikan setiap langganan hanya diproses sekali
                        .options(selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis))
                    )
                else:
                    # Normal mode (tanggal 5)
                    base_stmt = (
                        select(LanggananModel)
                        .join(
                            InvoiceModel,
                            LanggananModel.pelanggan_id == InvoiceModel.pelanggan_id,
                        )
                        .where(
                            InvoiceModel.tgl_jatuh_tempo == target_due_date,  # Cari yang jatuh tempo tepat tanggal 1
                            LanggananModel.status == "Aktif",
                            InvoiceModel.status_invoice == "Belum Dibayar",
                        )
                        .distinct(LanggananModel.id)  # Pastikan setiap langganan hanya diproses sekali
                        .options(selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis))
                    )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                overdue_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not overdue_batch:
                    break

                for langganan in overdue_batch:
                    suspend_type = "RETROACTIVE" if is_retroactive_day else "SCHEDULED"
                    logger.warning(f"⚠️ {suspend_type} SUSPEND: Melakukan suspend layanan untuk Langganan ID: {langganan.id} - Pelanggan: {langganan.pelanggan.nama}")

                    data_teknis = langganan.pelanggan.data_teknis
                    mikrotik_success = False
                    mikrotik_error_msg = None

                    # Opsi 2: Database First - Coba Mikrotik dulu tapi DB priority
                    if data_teknis:
                        try:
                            # 1. Coba update Mikrotik DULU (tapi tidak akan rollback DB jika gagal)
                            logger.info(f"🔄 Mencoba update Mikrotik untuk Langganan ID: {langganan.id}...")
                            await mikrotik_service.trigger_mikrotik_update(db, langganan, data_teknis, data_teknis.id_pelanggan)
                            mikrotik_success = True
                            logger.info(f"✅ Mikrotik update SUKSES untuk Langganan ID: {langganan.id}")

                        except Exception as mikrotik_error:
                            # Log error tapi LANJUTKAN proses DB (business priority)
                            mikrotik_error_msg = str(mikrotik_error)
                            logger.error(f"❌ Mikrotik update GAGAL untuk Langganan ID: {langganan.id}, tetapi suspend di DB akan tetap dijalankan. Error: {mikrotik_error}")

                            # Tandai untuk retry otomatis nanti
                            if data_teknis:
                                data_teknis.mikrotik_sync_pending = True
                                db.add(data_teknis)
                                logger.info(f"🔄 Ditandai untuk retry otomatis: Langganan ID {langganan.id}")
                    else:
                        logger.warning(f"⚠️ Data Teknis tidak ditemukan untuk langganan ID {langganan.id}, suspend hanya di DB.")

                    # 2. UPDATE DATABASE (Priority - pastikan ini selalu jalan)
                    try:
                        # Update invoice menjadi kadaluarsa
                        update_invoice_stmt = (
                            update(InvoiceModel)
                            .where(InvoiceModel.pelanggan_id == langganan.pelanggan_id)
                            .where(InvoiceModel.status_invoice == "Belum Dibayar")
                            .values(status_invoice="Kadaluarsa")
                        )
                        invoice_update_result: Result = await db.execute(update_invoice_stmt)
                        total_invoices_overdue += invoice_update_result.rowcount  # type: ignore

                        # Update langganan menjadi Suspended (ini PASTI jalan)
                        langganan.status = "Suspended"
                        db.add(langganan)

                        # Commit perubahan DB
                        await db.commit()
                        logger.info(f"✅ DB update SUKSES untuk Langganan ID: {langganan.id}. Status = Suspended.")

                        total_services_suspended += 1

                        if mikrotik_success:
                            logger.info(f"🔒 Layanan SUKSES di-suspend lengkap (DB + Mikrotik) untuk: {langganan.pelanggan.nama}")
                        else:
                            logger.warning(f"⚠️ Layanan di-suspend di DB saja (Mikrotik gagal) untuk: {langganan.pelanggan.nama}")
                            if mikrotik_error_msg:
                                logger.warning(f"📝 Mikrotik error detail: {mikrotik_error_msg}")

                    except Exception as db_error:
                        # Ini ERROR SEVERE - tidak bisa update DB
                        logger.error(f"❌ KRITIK: Gagal update DB untuk Langganan ID {langganan.id}. Error: {db_error}")
                        await db.rollback()
                        logger.error(f"🔄 Rollback DB SELESAI untuk Langganan ID: {langganan.id}.")
                        # Lanjut ke pelanggan berikutnya
                        continue

                offset += BATCH_SIZE

            except Exception as e:
                await db.rollback()
                logger.error(
                    f"[FAIL] Scheduler 'job_suspend_services' failed at offset {offset}. Details: {traceback.format_exc()}"
                )
                break

    if total_services_suspended > 0:
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            f"✅ Berhasil suspend {total_services_suspended} layanan dan mengubah {total_invoices_overdue} invoice menjadi Kadaluarsa. (Tanggal jatuh tempo: {target_due_date.strftime('%d %B %Y')})",
        )
    else:
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            f"✅ Tidak ada layanan baru untuk di-suspend. (Target tanggal jatuh tempo: {target_due_date.strftime('%d %B %Y')})",
        )


async def job_send_payment_reminders() -> None:
    """
    Job scheduler buat kirim pengingat pembayaran ke pelanggan.
    Jalan 3 hari sebelum jatuh tempo buat ngingetin pelanggan.

    Yang dilakuin:
    1. Cari pelanggan yang jatuh tempo 3 hari lagi
    2. Siapkan data pelanggan buat notifikasi
    3. (Placeholder) Kirim notifikasi via WhatsApp/Email
    4. Log jumlah pengingat yang dikirim

    Note: Saat ini masih placeholder, belum ada integrasi
    dengan WhatsApp gateway atau email service.
    Bisa ditambahi later dengan:
    - WhatsApp Business API
    - Email service (SendGrid, dll)
    - SMS gateway

    Performance:
    - Batch processing (100 records per batch)
    - Read-only operation (tidak ubah data)
    """
    log_scheduler_event(logger, "job_send_payment_reminders", "started")
    total_reminders_sent = 0
    target_due_date = date.today() + timedelta(days=3)
    BATCH_SIZE = 100
    offset = 0

    async with SessionType() as db:
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .where(
                        LanggananModel.tgl_jatuh_tempo == target_due_date,
                        LanggananModel.status == "Aktif",
                    )
                    .options(selectinload(LanggananModel.pelanggan))
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                reminder_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not reminder_batch:
                    break

                for langganan in reminder_batch:
                    pelanggan = langganan.pelanggan
                    logger.info(f"Mengirim pengingat pembayaran untuk pelanggan ID: {pelanggan.id} ({pelanggan.nama})")
                    # Di sini Anda bisa menambahkan logika pengiriman notifikasi (WA, Email, dll)
                    total_reminders_sent += 1

                # Tidak ada db.commit() karena kita hanya membaca data
                offset += BATCH_SIZE

            except Exception as e:
                logger.error(
                    f"[FAIL] Scheduler 'job_send_payment_reminders' failed at offset {offset}. Details: {traceback.format_exc()}"
                )
                break

    if total_reminders_sent > 0:
        log_scheduler_event(
            logger,
            "job_send_payment_reminders",
            "completed",
            f"Berhasil mengirim {total_reminders_sent} pengingat pembayaran.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_send_payment_reminders",
            "completed",
            "Tidak ada pelanggan untuk dikirim pengingat hari ini.",
        )


async def job_verify_payments() -> None:
    """
    Job scheduler buat cek dan rekonsiliasi pembayaran yang mungkin terlewat.
    Kadang ada pembayaran yang masuk tapi callback dari Xendit gagal diterima.

    Tugasnya:
    1. Cek pembayaran yang udah lunas di Xendit (3 hari terakhir)
    2. Bandingin dengan status di database
    3. Proses pembayaran yang belum tercatat di sistem
    4. Update status invoice jadi 'Lunas'
    5. Trigger aktifasi layanan kalau pelanggan sebelumnya suspend

    Ini penting buat antisipasi:
    - Webhook callback yang gagal
    - Network issues saat pembayaran
    - Payment gateway yang lagi ada masalah

    Integration:
    - Xendit API untuk cek status pembayaran
    - Payment processing logic
    - Mikrotik service buat re-activation

    Performance:
    - Eager loading semua relasi yang dibutuhkan
    - Transaction safety dengan rollback
    """
    log_scheduler_event(logger, "job_verify_payments", "started")

    async with SessionType() as db:
        try:
            # Bagian 1: Logika Kadaluarsa SUDAH DIHAPUS DARI SINI

            # Bagian 2: Rekonsiliasi Pembayaran Terlewat
            paid_invoice_ids = await xendit_service.get_paid_invoice_ids_since(days=3)

            if not paid_invoice_ids:
                log_scheduler_event(
                    logger,
                    "job_verify_payments",
                    "completed",
                    "Tidak ada pembayaran baru di Xendit.",
                )
                await db.commit()  # Tetap commit untuk menutup transaksi
                return

            # PERBAIKAN: Eager load semua relasi yang dibutuhkan oleh _process_successful_payment
            unprocessed_stmt = (
                select(InvoiceModel)
                .where(
                    InvoiceModel.xendit_external_id.in_(paid_invoice_ids),
                    InvoiceModel.status_invoice != "Lunas",
                )
                .options(
                    selectinload(InvoiceModel.pelanggan).options(
                        selectinload(PelangganModel.harga_layanan),
                        selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                        selectinload(PelangganModel.data_teknis),
                    )
                )
            )
            invoices_to_process = (await db.execute(unprocessed_stmt)).scalars().unique().all()

            processed_count = 0
            if invoices_to_process:
                logger.warning(f"[VERIFY] Menemukan {len(invoices_to_process)} pembayaran terlewat. Memproses...")
                for invoice in invoices_to_process:
                    await _process_successful_payment(db, invoice)
                    processed_count += 1

            await db.commit()
            log_scheduler_event(
                logger,
                "job_verify_payments",
                "completed",
                f"Memproses {processed_count} pembayaran terlewat.",
            )

        except Exception as e:
            await db.rollback()
            error_details = traceback.format_exc()
            logger.error(f"[FAIL] Scheduler 'job_verify_payments' failed. Details:\n{error_details}")


async def job_retry_failed_invoices() -> None:
    """
    Job scheduler buat retry invoice yang gagal dibuat payment link-nya.
    Fokus pada invoice yang belum ada payment_link atau xendit_id-nya.

    Logic yang dijalanin:
    1. Cari invoice yang belum punya payment link (xendit_id = NULL)
    2. Cek jumlah retry yang sudah dilakukan (max 3 kali)
    3. Coba buat payment link lagi ke Xendit
    4. Update status invoice jika berhasil
    5. Notifikasi admin jika masih gagal setelah max retry

    Aturan retry:
    - Max 3 kali percobaan
    - Interval 1 jam antara retry
    - Skip invoice yang sudah lunas
    - Log semua retry attempts

    Integration:
    - Xendit API untuk pembuatan payment link
    - Email/notifikasi ke admin untuk monitoring
    - Database update untuk tracking status
    """
    log_scheduler_event(logger, "job_retry_failed_invoices", "started")

    MAX_RETRY = 3
    RETRY_INTERVAL_HOURS = 1
    BATCH_SIZE = 50
    offset = 0
    total_retried = 0
    total_success = 0
    total_failed = 0

    async with SessionType() as db:
        while True:
            try:
                # Cari invoice yang gagal (belum ada xendit_id)
                stmt = (
                    select(InvoiceModel)
                    .where(
                        InvoiceModel.xendit_id.is_(None),
                        InvoiceModel.status_invoice == "Belum Dibayar",
                        InvoiceModel.xendit_retry_count < MAX_RETRY,
                    )
                    .where(
                        # Cek interval retry (1 jam sejak retry terakhir)
                        (InvoiceModel.xendit_last_retry.is_(None)) |
                        (
                            InvoiceModel.xendit_last_retry <
                            datetime.now() - timedelta(hours=RETRY_INTERVAL_HOURS)
                        )
                    )
                    .options(
                        selectinload(InvoiceModel.pelanggan).options(
                            selectinload(PelangganModel.harga_layanan),
                            selectinload(PelangganModel.data_teknis),
                            selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                        )
                    )
                    .order_by(InvoiceModel.created_at.desc())  # Prioritaskan yang paling lama
                )

                batch_stmt = stmt.offset(offset).limit(BATCH_SIZE)
                failed_invoices = (await db.execute(batch_stmt)).scalars().unique().all()

                if not failed_invoices:
                    break

                for invoice in failed_invoices:
                    try:
                        logger.info(f"🔄 Retrying invoice {invoice.invoice_number} (attempt {invoice.xendit_retry_count + 1}/{MAX_RETRY})")

                        # Update status ke processing
                        invoice.xendit_status = "processing"
                        invoice.xendit_last_retry = datetime.now()
                        db.add(invoice)
                        await db.flush()

                        # Siapkan data untuk retry
                        pelanggan = invoice.pelanggan
                        paket = pelanggan.langganan[0].paket_layanan if pelanggan.langganan else None
                        brand = pelanggan.harga_layanan

                        if not all([pelanggan, paket, brand]):
                            raise ValueError("Data tidak lengkap untuk retry invoice")

                        # Generate deskripsi yang sama seperti saat pembuatan awal
                        jatuh_tempo_str = datetime.combine(invoice.tgl_jatuh_tempo, datetime.min.time()).strftime("%d/%m/%Y")
                        deskripsi_xendit = (
                            f"Biaya berlangganan internet up to {paket.kecepatan if paket else 'N/A'} Mbps "
                            f"jatuh tempo pembayaran tanggal {jatuh_tempo_str}"
                        )

                        # Hitung pajak
                        pajak_persen = float(brand.pajak) if brand else 0.0
                        harga_dasar = float(paket.harga if paket else 0.0)
                        pajak = math.floor(harga_dasar * (pajak_persen / 100) + 0.5)

                        no_telp_xendit = f"+62{pelanggan.no_telp.lstrip('0')}" if pelanggan.no_telp else ""

                        # Coba buat payment link lagi
                        xendit_response = await create_invoice_with_rate_limit(
                            invoice=invoice,
                            pelanggan=pelanggan,
                            paket=paket,
                            deskripsi_xendit=deskripsi_xendit,
                            pajak=pajak,
                            no_telp_xendit=no_telp_xendit,
                            priority=InvoicePriority.NORMAL  # Lower priority untuk retry
                        )

                        # Validasi response
                        if not xendit_response or not xendit_response.get("id"):
                            raise ValueError(f"Invalid Xendit response: {xendit_response}")

                        # Update invoice dengan payment link
                        invoice.payment_link = xendit_response.get("short_url", xendit_response.get("invoice_url"))
                        invoice.xendit_id = xendit_response.get("id")
                        invoice.xendit_external_id = xendit_response.get("external_id")
                        invoice.xendit_status = "completed"
                        invoice.xendit_error_message = None

                        db.add(invoice)
                        logger.info(f"✅ Invoice {invoice.invoice_number} BERHASIL dibuatkan payment link")
                        logger.info(f"📱 Payment link: {invoice.payment_link}")
                        logger.info(f"📱 WhatsApp notification sent to: {pelanggan.nama} ({pelanggan.no_telp})")

                        total_success += 1

                    except Exception as retry_error:
                        # Increment retry count
                        invoice.xendit_retry_count += 1
                        invoice.xendit_status = "failed"
                        invoice.xendit_error_message = str(retry_error)

                        db.add(invoice)

                        if invoice.xendit_retry_count >= MAX_RETRY:
                            total_failed += 1
                            logger.error(f"❌ Invoice {invoice.invoice_number} GAGAL setelah {MAX_RETRY} kali retry: {retry_error}")
                            logger.error(f"📧 Mohon hubungi pelanggan {pelanggan.nama} secara manual")
                        else:
                            logger.warning(f"⚠️ Invoice {invoice.invoice_number} retry {invoice.xendit_retry_count}/{MAX_RETRY} gagal: {retry_error}")

                    total_retried += 1

                await db.commit()
                offset += BATCH_SIZE

            except Exception as e:
                await db.rollback()
                logger.error(f"[FAIL] Scheduler 'job_retry_failed_invoices' failed at offset {offset}. Details: {traceback.format_exc()}")
                break

    # Log hasil proses
    if total_retried > 0:
        log_scheduler_event(
            logger,
            "job_retry_failed_invoices",
            "completed",
            f"Processed {total_retried} invoices: {total_success} success, {total_failed} failed",
        )

        # Notifikasi admin jika ada yang masih gagal
        if total_failed > 0:
            logger.warning(f"🚨 ADMIN ALERT: {total_failed} invoices still failed after {MAX_RETRY} retries")
            logger.warning("📧 Mohon periksa dan hubungi pelanggan secara manual")

            # Kirim notifikasi real-time ke admin
            try:
                notification_data = {
                    "title": "🚨 Invoice Retry Failed",
                    "message": f"{total_failed} invoice masih gagal setelah {MAX_RETRY} kali retry. Mohon periksa dan hubungi pelanggan secara manual.",
                    "type": "error",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "failed_count": total_failed,
                        "max_retry": MAX_RETRY,
                        "action_url": "/invoices?filter=failed"
                    }
                }
                # Dapatkan semua user dengan role admin dan super_admin
                admin_users = manager.get_users_by_role("admin")
                super_admin_users = manager.get_users_by_role("super_admin")
                all_admin_users = list(set(admin_users + super_admin_users))  # Remove duplicates

                if all_admin_users:
                    await manager.broadcast_to_roles(notification_data, all_admin_users)
                    logger.info(f"📢 Notifikasi error terkirim ke {len(all_admin_users)} admin via WebSocket")
                else:
                    logger.warning("⚠️ Tidak ada admin user yang aktif untuk notifikasi")
            except Exception as notif_error:
                logger.error(f"Gagal mengirim notifikasi ke admin: {notif_error}")
    else:
        log_scheduler_event(
            logger,
            "job_retry_failed_invoices",
            "completed",
            "No failed invoices to retry.",
        )


async def job_retry_mikrotik_syncs() -> None:
    """
    Job scheduler buat retry sync ke Mikrotik yang sebelumnya gagal.
    Kadang network lagi bermasalah atau Mikrotik server lagi down.

    Yang dikerjain:
    1. Cari semua data teknis yang flag-nya 'sync_pending = true'
    2. Coba sync ulang ke Mikrotik server
    3. Kalau berhasil, reset flag jadi false
    4. Kalau masih gagal, biarkan flag true buat coba lagi nanti

    Kenapa perlu ini?
    - Network intermittent yang bikin API call gagal
    - Mikrotik server yang lagi restart/maintenance
    - Rate limiting dari Mikrotik API
    - Connection timeout

    Error handling:
    - Tetap coba semua item meski ada yang gagal
    - Log error buat setiap item yang gagal
    - Tidak rollback keseluruhan transaction

    Integration:
    - Mikrotik API via mikrotik_service
    - Database flags buat tracking sync status
    - Error logging buat monitoring
    """
    log_scheduler_event(logger, "job_retry_mikrotik_syncs", "started")
    total_retried = 0
    async with SessionType() as db:
        try:
            # Cari semua data teknis yang sinkronisasinya tertunda
            stmt = (
                select(DataTeknisModel)
                .where(DataTeknisModel.mikrotik_sync_pending == True)
                .options(selectinload(DataTeknisModel.pelanggan).selectinload(PelangganModel.langganan))
            )
            pending_syncs = (await db.execute(stmt)).scalars().all()

            if not pending_syncs:
                log_scheduler_event(
                    logger,
                    "job_retry_mikrotik_syncs",
                    "completed",
                    "No pending Mikrotik syncs.",
                )
                return

            logger.info(f"Found {len(pending_syncs)} pending Mikrotik syncs to retry.")
            for data_teknis in pending_syncs:
                try:
                    langganan = data_teknis.pelanggan.langganan[0]
                    # Coba jalankan lagi fungsi update ke Mikrotik DENGAN ARGUMEN LENGKAP
                    await mikrotik_service.trigger_mikrotik_update(db, langganan, data_teknis, data_teknis.id_pelanggan)

                    # Jika berhasil, set flag kembali ke False
                    setattr(data_teknis, 'mikrotik_sync_pending', False)
                    db.add(data_teknis)
                    logger.info(f"Successfully synced pending update for Data Teknis ID: {data_teknis.id}")
                    total_retried += 1
                except Exception as e:
                    # Jika masih gagal, biarkan flag tetap True dan catat error
                    logger.error(f"Still failing to sync Mikrotik for Data Teknis ID {data_teknis.id}: {e}")

            await db.commit()
            log_scheduler_event(
                logger,
                "job_retry_mikrotik_syncs",
                "completed",
                f"Successfully retried {total_retried} syncs.",
            )
        except Exception as e:
            await db.rollback()
            logger.error(f"[FAIL] Scheduler 'job_retry_mikrotik_syncs' encountered an error: {traceback.format_exc()}")


# ====================================================================
# LOCATION-BASED BATCH SUSPEND
# ====================================================================
# Modifikasi dari job_suspend_services untuk batch processing per lokasi
# dengan mempertahankan system yang ada (Database First, Mikrotik Second)

async def job_suspend_services_by_location() -> None:
    """
    Location-based batch suspend dengan mempertahankan existing logic.
    Memproses suspend per lokasi (Tambun, Cibitung, Cikarang, dll) dengan batch processing.

    Alur:
    1. Get lokasi-lokasi yang ada pelanggan overdue
    2. Process lokasi secara sequential sesuai priority
    3. Dalam setiap lokasi, process pelanggan dalam batch
    4. Mikrotik dan Database processing tetap seperti existing logic
    """
    from sqlalchemy import text
    import asyncio

    logger.info("🚀 Starting LOCATION-BASED BATCH SUSPEND...")

    # Settings untuk location batch - akan diambil dari database
    MAX_BATCH_SIZE_PER_LOCATION = 30
    DELAY_BETWEEN_LOCATIONS = 2.0  # detik
    DELAY_BETWEEN_BATCHES = 1.0   # detik
    MAX_CONCURRENT_MIKROTIK = 5   # parallel operations

    # Get locations dynamically from database (pelanggan.alamat)
    async def get_locations_from_database(db, target_date):
        """Get lokasi dari database, diurutkan berdasarkan jumlah pelanggan terbanyak"""
        location_query = text("""
            SELECT p.alamat, COUNT(l.id) as customer_count
            FROM pelanggan p
            JOIN langganan l ON p.id = l.pelanggan_id
            JOIN invoice i ON l.pelanggan_id = i.pelanggan_id
            WHERE l.status = 'Aktif'
            AND i.status_invoice = 'Belum Dibayar'
            AND i.tgl_jatuh_tempo = :target_date
            AND p.alamat IS NOT NULL
            AND p.alamat != ''
            GROUP BY p.alamat
            HAVING COUNT(l.id) > 0
            ORDER BY customer_count DESC, p.alamat ASC
        """)

        result = await db.execute(location_query, {"target_date": target_date})
        locations_with_count = [(row[0], row[1]) for row in result.fetchall()]

        # Log location counts untuk monitoring
        logger.info(f"📍 Found locations with overdue customers:")
        for loc, count in locations_with_count[:10]:  # Show top 10
            logger.info(f"   🏠 {loc}: {count} customers (will be processed first)")

        if len(locations_with_count) > 10:
            logger.info(f"   ... and {len(locations_with_count) - 10} more locations")

        # Return only location names, sorted by customer count (prioritas yang paling banyak)
        return [loc for loc, count in locations_with_count]

    total_stats = {
        'total_locations': 0,
        'total_customers': 0,
        'mikrotik_success': 0,
        'mikrotik_failed': 0,
        'database_success': 0,
        'database_failed': 0,
        'requires_manual_sync': 0,
        'processed_locations': [],
        'failed_locations': []
    }

    current_date = date.today()

    # Logic tanggal yang sama dengan existing function
    is_main_suspend_day = current_date.day == 5
    is_retroactive_day = 6 <= current_date.day <= 10

    if not (is_main_suspend_day or is_retroactive_day):
        log_scheduler_event(
            logger,
            "job_suspend_services_by_location",
            "completed",
            f"Hari ini tanggal {current_date.day}, suspend hanya dilakukan tanggal 5-10 (retroactive).",
        )
        return

    suspend_type = "RETROACTIVE" if is_retroactive_day else "SCHEDULED"
    target_due_date = date(current_date.year, current_date.month, 1)

    logger.info(f"🎯 {suspend_type} LOCATION-BATCH SUSPEND: Target {target_due_date.strftime('%d %B %Y')}")

    async with SessionType() as db:
        try:
            # Step 1: Get lokasi dari database secara dinamis, diurutkan berdasarkan jumlah pelanggan
            logger.info("📍 Getting locations from database, sorted by customer count...")

            # Gunakan fungsi dinamis untuk get lokasi
            sorted_locations = await get_locations_from_database(db, target_due_date)

            if not sorted_locations:
                logger.info("✅ No locations with overdue customers found")
                return

            total_stats['total_locations'] = len(sorted_locations)
            logger.info(f"📍 Processing {len(sorted_locations)} locations in order of customer count")

            # Step 2: Process setiap lokasi secara sequential
            for loc_idx, location in enumerate(sorted_locations, 1):
                logger.info(f"🎯 [{loc_idx}/{len(sorted_locations)}] Processing location: {location}")

                try:
                    # Get pelanggan untuk lokasi ini
                    customers_query = text("""
                        SELECT
                            l.id as langganan_id,
                            p.id as pelanggan_id,
                            p.nama as pelanggan_nama,
                            p.alamat as pelanggan_alamat,
                            l.status as langganan_status,
                            i.id as invoice_id,
                            i.invoice_number as invoice_number,
                            i.status_invoice as invoice_status,
                            i.tgl_jatuh_tempo as due_date,
                            dt.id as data_teknis_id,
                            dt.id_pelanggan as mikrotik_id,
                            dt.mikrotik_server as mikrotik_server,
                            dt.mikrotik_sync_pending as sync_pending
                        FROM pelanggan p
                        JOIN langganan l ON p.id = l.pelanggan_id
                        JOIN invoice i ON l.pelanggan_id = i.pelanggan_id
                        LEFT JOIN data_teknis dt ON p.id = dt.pelanggan_id
                        WHERE l.status = 'Aktif'
                        AND i.status_invoice = 'Belum Dibayar'
                        AND i.tgl_jatuh_tempo = :target_date
                        AND p.alamat = :location
                        ORDER BY p.nama
                    """)

                    customer_result = await db.execute(customers_query, {
                        "target_date": target_due_date,
                        "location": location
                    })
                    customers = [dict(row._mapping) for row in customer_result.fetchall()]

                    if not customers:
                        logger.info(f"✅ No overdue customers in {location}")
                        continue

                    logger.info(f"📊 Found {len(customers)} customers to suspend in {location}")
                    location_stats = {
                        'total_customers': len(customers),
                        'mikrotik_success': 0,
                        'mikrotik_failed': 0,
                        'database_success': 0,
                        'database_failed': 0,
                        'requires_manual_sync': 0
                    }

                    # Process dalam batch untuk lokasi ini
                    for batch_start in range(0, len(customers), MAX_BATCH_SIZE_PER_LOCATION):
                        batch_customers = customers[batch_start:batch_start + MAX_BATCH_SIZE_PER_LOCATION]
                        batch_num = (batch_start // MAX_BATCH_SIZE_PER_LOCATION) + 1

                        logger.info(f"🔄 {location} - Batch {batch_num}: {len(batch_customers)} customers")

                        # Load langganan objects untuk batch ini
                        langganan_objects = []
                        for customer in batch_customers:
                            try:
                                langganan_result = await db.execute(
                                    select(LanggananModel)
                                    .options(selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis))
                                    .where(LanggananModel.id == customer['langganan_id'])
                                )
                                langganan_obj = langganan_result.scalar_one_or_none()
                                if langganan_obj:
                                    langganan_objects.append({
                                        'data': customer,
                                        'object': langganan_obj
                                    })
                            except Exception as e:
                                logger.error(f"❌ Error loading langganan {customer['pelanggan_nama']}: {e}")
                                location_stats['database_failed'] += 1

                        # Step 3: Mikrotik suspend (parallel) - Existing logic
                        async def suspend_single_mikrotik(customer_info):
                            data = customer_info['data']
                            langganan_obj = customer_info['object']

                            try:
                                data_teknis = langganan_obj.pelanggan.data_teknis

                                if not data_teknis or not data_teknis.id_pelanggan:
                                    return {'success': False, 'error': 'No Mikrotik data', 'requires_sync': False}

                                logger.info(f"🔄 [Mikrotik] Suspending: {data['pelanggan_nama']} ({data['mikrotik_id']})")

                                # Existing Mikrotik logic
                                await mikrotik_service.trigger_mikrotik_update(
                                    db=None,  # No DB context for Mikrotik-only
                                    langganan=langganan_obj,
                                    data_teknis=data_teknis,
                                    old_id_pelanggan=data['mikrotik_id']
                                )

                                return {'success': True, 'error': None, 'requires_sync': False}

                            except Exception as e:
                                logger.error(f"❌ [Mikrotik] Failed {data['pelanggan_nama']}: {str(e)}")
                                return {'success': False, 'error': str(e), 'requires_sync': True}

                        # Execute Mikrotik suspends dengan concurrency limit
                        semaphore = asyncio.Semaphore(MAX_CONCURRENT_MIKROTIK)

                        async def controlled_suspend(customer_info):
                            async with semaphore:
                                return await suspend_single_mikrotik(customer_info)

                        mikrotik_results = await asyncio.gather(
                            *[controlled_suspend(info) for info in langganan_objects],
                            return_exceptions=True
                        )

                        # Handle exceptions
                        processed_mikrotik = []
                        for result in mikrotik_results:
                            if isinstance(result, Exception):
                                processed_mikrotik.append({'success': False, 'error': str(result), 'requires_sync': True})
                            else:
                                processed_mikrotik.append(result)

                        # Step 4: Database update (batch atomic) - Existing logic
                        try:
                            invoice_ids = [cust['invoice_id'] for cust in batch_customers]
                            langganan_ids = [cust['langganan_id'] for cust in batch_customers]
                            sync_pending_updates = []

                            for i, customer in enumerate(batch_customers):
                                if not processed_mikrotik[i]['success'] and customer.get('mikrotik_id'):
                                    sync_pending_updates.append({
                                        'data_teknis_id': customer['data_teknis_id'],
                                        'sync_pending': True
                                    })

                            # Batch database updates
                            if invoice_ids:
                                await db.execute(
                                    update(InvoiceModel)
                                    .where(InvoiceModel.id.in_(invoice_ids))
                                    .values(status_invoice="Kadaluarsa")
                                )

                            if langganan_ids:
                                await db.execute(
                                    update(LanggananModel)
                                    .where(LanggananModel.id.in_(langganan_ids))
                                    .values(status="Suspended")
                                )

                            if sync_pending_updates:
                                data_teknis_ids = [update['data_teknis_id'] for update in sync_pending_updates]
                                await db.execute(
                                    update(DataTeknisModel)
                                    .where(DataTeknisModel.id.in_(data_teknis_ids))
                                    .values(mikrotik_sync_pending=True)
                                )

                            await db.commit()

                            # Update statistics
                            for i, result in enumerate(processed_mikrotik):
                                if result['success']:
                                    location_stats['mikrotik_success'] += 1
                                else:
                                    location_stats['mikrotik_failed'] += 1
                                    if result['requires_sync']:
                                        location_stats['requires_manual_sync'] += 1

                                location_stats['database_success'] += 1

                            logger.info(f"✅ {location} - Batch {batch_num} completed successfully")

                        except Exception as e:
                            logger.error(f"❌ {location} - Batch {batch_num} DB update failed: {str(e)}")
                            await db.rollback()
                            location_stats['database_failed'] += len(batch_customers)
                            for result in processed_mikrotik:
                                if not result['success']:
                                    location_stats['mikrotik_failed'] += 1
                                    if result['requires_sync']:
                                        location_stats['requires_manual_sync'] += 1

                        # Delay between batches (except last batch)
                        if batch_start + MAX_BATCH_SIZE_PER_LOCATION < len(customers):
                            await asyncio.sleep(DELAY_BETWEEN_BATCHES)

                    # Update total statistics
                    total_stats['total_customers'] += location_stats['total_customers']
                    total_stats['mikrotik_success'] += location_stats['mikrotik_success']
                    total_stats['mikrotik_failed'] += location_stats['mikrotik_failed']
                    total_stats['database_success'] += location_stats['database_success']
                    total_stats['database_failed'] += location_stats['database_failed']
                    total_stats['requires_manual_sync'] += location_stats['requires_manual_sync']

                    total_stats['processed_locations'].append({
                        'location': location,
                        'customers': location_stats['total_customers'],
                        'success': location_stats['database_failed'] == 0
                    })

                    logger.info(f"✅ [{loc_idx}/{len(sorted_locations)}] Completed {location}:")
                    logger.info(f"   Customers: {location_stats['total_customers']}")
                    logger.info(f"   Mikrotik Success: {location_stats['mikrotik_success']}")
                    logger.info(f"   Database Success: {location_stats['database_success']}")

                    # Delay between locations (except last location)
                    if loc_idx < len(sorted_locations):
                        logger.info(f"⏳ Waiting {DELAY_BETWEEN_LOCATIONS}s before next location...")
                        await asyncio.sleep(DELAY_BETWEEN_LOCATIONS)

                except Exception as e:
                    logger.error(f"❌ Failed to process location {location}: {str(e)}")
                    total_stats['failed_locations'].append({
                        'location': location,
                        'customers': 0,
                        'success': False,
                        'error': str(e)
                    })

            # Final summary
            logger.info("🎉 LOCATION-BASED SUSPEND SUMMARY:")
            logger.info(f"   📅 Target Date: {target_due_date.strftime('%d %B %Y')}")
            logger.info(f"   📍 Total Locations: {total_stats['total_locations']}")
            logger.info(f"   👥 Total Customers: {total_stats['total_customers']}")
            logger.info(f"   ✅ Mikrotik Success: {total_stats['mikrotik_success']}")
            logger.info(f"   ❌ Mikrotik Failed: {total_stats['mikrotik_failed']}")
            logger.info(f"   💾 Database Success: {total_stats['database_success']}")
            logger.info(f"   💥 Database Failed: {total_stats['database_failed']}")
            logger.info(f"   🔧 Requires Manual Sync: {total_stats['requires_manual_sync']}")

            if total_stats['processed_locations']:
                logger.info(f"   ✅ Successfully Processed:")
                for loc in total_stats['processed_locations']:
                    status = "✅" if loc['success'] else "❌"
                    logger.info(f"      {status} {loc['location']}: {loc['customers']} customers")

            if total_stats['failed_locations']:
                logger.warning(f"   ⚠️ Failed Locations:")
                for loc in total_stats['failed_locations']:
                    logger.info(f"      ❌ {loc['location']}: {loc.get('customers', 0)} customers")

            if total_stats['requires_manual_sync'] > 0:
                logger.warning(f"⚠️ {total_stats['requires_manual_sync']} customers require manual Mikrotik sync!")

            logger.info("✅ Location-based batch suspend completed successfully!")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Critical error in location-based suspend: {str(e)}")
            raise
