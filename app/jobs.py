# app/jobs.py

import logging
import traceback
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
import uuid
import math
from .database import get_db

# Impor komponen
from .database import AsyncSessionLocal as SessionLocal
from .models import (
    Langganan as LanggananModel,
    Invoice as InvoiceModel,
    Pelanggan as PelangganModel,
)
from .services import mikrotik_service, xendit_service
from .logging_config import log_scheduler_event
from .routers.invoice import _process_successful_payment
from .models import DataTeknis as DataTeknisModel
from .routers.invoice import update_overdue_invoices

logger = logging.getLogger("app.jobs")


# Fungsi generate_single_invoice tetap sama, tidak perlu diubah
async def generate_single_invoice(db, langganan: LanggananModel):
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

        new_invoice_data = {
            "invoice_number": f"INV-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
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
        db.add(db_invoice)
        await db.flush()

        deskripsi_xendit = ""
        jatuh_tempo_str_lengkap = db_invoice.tgl_jatuh_tempo.strftime("%d/%m/%Y")

        if langganan.metode_pembayaran == "Prorate":
            # ▼▼▼ LOGIKA BARU DIMULAI DI SINI ▼▼▼

            # Hitung harga normal untuk perbandingan
            harga_normal_full = float(paket.harga) * (1 + (float(brand.pajak) / 100))

            # Cek apakah ini invoice gabungan
            if db_invoice.total_harga > (harga_normal_full + 1):
                # INI TAGIHAN GABUNGAN
                start_day = db_invoice.tgl_invoice.day
                end_day = db_invoice.tgl_jatuh_tempo.day
                periode_prorate_str = db_invoice.tgl_jatuh_tempo.strftime("%B %Y")
                periode_berikutnya_str = (
                    db_invoice.tgl_jatuh_tempo + relativedelta(months=1)
                ).strftime("%B %Y")

                deskripsi_xendit = (
                    f"Biaya internet up to {paket.kecepatan} Mbps. "
                    f"Periode Prorate {start_day}-{end_day} {periode_prorate_str} + "
                    f"Periode {periode_berikutnya_str}"
                )
            else:
                # INI TAGIHAN PRORATE BIASA
                start_day = db_invoice.tgl_invoice.day
                end_day = db_invoice.tgl_jatuh_tempo.day
                periode_str = db_invoice.tgl_jatuh_tempo.strftime("%B %Y")
                deskripsi_xendit = (
                    f"Biaya berlangganan internet up to {paket.kecepatan} Mbps, "
                    f"Periode Tgl {start_day}-{end_day} {periode_str}"
                )

        else:  # Otomatis
            deskripsi_xendit = (
                f"Biaya berlangganan internet up to {paket.kecepatan} Mbps "
                f"jatuh tempo pembayaran tanggal {jatuh_tempo_str_lengkap}"
            )

        no_telp_xendit = (
            f"+62{pelanggan.no_telp.lstrip('0')}" if pelanggan.no_telp else None
        )

        xendit_response = await xendit_service.create_xendit_invoice(
            db_invoice, pelanggan, paket, deskripsi_xendit, pajak, no_telp_xendit
        )

        db_invoice.payment_link = xendit_response.get(
            "short_url", xendit_response.get("invoice_url")
        )
        db_invoice.xendit_id = xendit_response.get("id")
        db_invoice.xendit_external_id = xendit_response.get("external_id")

        db.add(db_invoice)
        logger.info(
            f"Invoice {db_invoice.invoice_number} berhasil dibuat untuk Langganan ID {langganan.id}"
        )

    except Exception as e:
        logger.error(
            f"Gagal membuat invoice untuk Langganan ID {langganan.id}: {e}\n{traceback.format_exc()}"
        )


# ==========================================================
# --- JOB SCHEDULER YANG SUDAH DIOPTIMALKAN ---
# ==========================================================


async def job_generate_invoices():
    log_scheduler_event(logger, "job_generate_invoices", "started")
    target_due_date = date.today() + timedelta(days=5)
    total_invoices_created = 0
    BATCH_SIZE = 100
    offset = 0

    async with SessionLocal() as db:
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .where(
                        LanggananModel.tgl_jatuh_tempo == target_due_date,
                        LanggananModel.status == "Aktif",
                    )
                    .options(
                        selectinload(LanggananModel.pelanggan).selectinload(
                            PelangganModel.harga_layanan
                        ),
                        selectinload(LanggananModel.pelanggan).selectinload(
                            PelangganModel.data_teknis
                        ),
                        selectinload(LanggananModel.paket_layanan),
                    )
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                subscriptions_batch = (
                    (await db.execute(batch_stmt)).scalars().unique().all()
                )

                if not subscriptions_batch:
                    break

                # OPTIMISASI: Ambil semua invoice yang sudah ada untuk batch ini dalam satu query
                pelanggan_ids_in_batch = [s.pelanggan_id for s in subscriptions_batch]
                existing_invoices_stmt = select(InvoiceModel.pelanggan_id).where(
                    InvoiceModel.pelanggan_id.in_(pelanggan_ids_in_batch),
                    InvoiceModel.tgl_jatuh_tempo == target_due_date,
                )
                existing_invoices_pelanggan_ids = {
                    row[0] for row in await db.execute(existing_invoices_stmt)
                }

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
                logger.error(
                    f"[FAIL] Scheduler 'job_generate_invoices' failed at offset {offset}. Details:\n{error_details}"
                )
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


async def job_suspend_services():
    """
    Tugas untuk men-suspend layanan dan mengubah status invoice menjadi 'Kadaluarsa'.
    Berjalan setiap hari untuk menonaktifkan pelanggan yang telat bayar.
    """
    log_scheduler_event(logger, "job_suspend_services", "started")
    total_services_suspended = 0
    total_invoices_overdue = 0
    current_date = date.today()
    BATCH_SIZE = 50
    offset = 0

    # Aturan: Layanan di-suspend pada hari ke-5 jika jatuh tempo tgl 1.
    # Artinya, jika hari ini tgl 5, kita cari yg jatuh tempo tgl 1 (selisih 4 hari).
    overdue_date_threshold = current_date - timedelta(days=4)

    async with SessionLocal() as db:
        while True:
            try:
                base_stmt = (
                    select(LanggananModel)
                    .join(
                        InvoiceModel,
                        LanggananModel.pelanggan_id == InvoiceModel.pelanggan_id,
                    )
                    .where(
                        InvoiceModel.tgl_jatuh_tempo <= overdue_date_threshold,
                        LanggananModel.status == "Aktif",
                        InvoiceModel.status_invoice == "Belum Dibayar",
                    )
                    .distinct(
                        LanggananModel.id
                    )  # <-- TAMBAHAN: Pastikan setiap langganan hanya diproses sekali
                    .options(
                        selectinload(LanggananModel.pelanggan).selectinload(
                            PelangganModel.data_teknis
                        )
                    )
                )

                batch_stmt = base_stmt.offset(offset).limit(BATCH_SIZE)
                overdue_batch = (await db.execute(batch_stmt)).scalars().unique().all()

                if not overdue_batch:
                    break

                for langganan in overdue_batch:
                    logger.warning(
                        f"Melakukan suspend layanan untuk Langganan ID: {langganan.id}..."
                    )

                    # 1. Ubah status invoice terkait menjadi 'Kadaluarsa'
                    # Ini lebih efisien daripada menjalankan job terpisah.
                    update_invoice_stmt = (
                        update(InvoiceModel)
                        .where(InvoiceModel.pelanggan_id == langganan.pelanggan_id)
                        .where(InvoiceModel.status_invoice == "Belum Dibayar")
                        .values(status_invoice="Kadaluarsa")
                    )
                    invoice_update_result = await db.execute(update_invoice_stmt)
                    total_invoices_overdue += invoice_update_result.rowcount

                    # 2. Ubah status langganan menjadi 'Suspended'
                    langganan.status = "Suspended"
                    db.add(langganan)

                    data_teknis = langganan.pelanggan.data_teknis
                    if data_teknis:
                        await mikrotik_service.trigger_mikrotik_update(
                            db, langganan, data_teknis, data_teknis.id_pelanggan
                        )
                        total_services_suspended += 1
                    else:
                        logger.error(
                            f"Data Teknis tidak ditemukan untuk langganan ID {langganan.id}, skip update Mikrotik."
                        )

                await db.commit()
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
            f"Berhasil suspend {total_services_suspended} layanan dan mengubah {total_invoices_overdue} invoice menjadi Kadaluarsa.",
        )
    else:
        log_scheduler_event(
            logger,
            "job_suspend_services",
            "completed",
            "Tidak ada layanan baru untuk di-suspend.",
        )


async def job_send_payment_reminders():
    log_scheduler_event(logger, "job_send_payment_reminders", "started")
    total_reminders_sent = 0
    target_due_date = date.today() + timedelta(days=3)
    BATCH_SIZE = 100
    offset = 0

    async with SessionLocal() as db:
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
                    logger.info(
                        f"Mengirim pengingat pembayaran untuk pelanggan ID: {pelanggan.id} ({pelanggan.nama})"
                    )
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


async def job_verify_payments():
    """Job HANYA untuk rekonsiliasi pembayaran yang terlewat via Xendit."""
    log_scheduler_event(logger, "job_verify_payments", "started")

    async with SessionLocal() as db:
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
                        selectinload(PelangganModel.langganan).selectinload(
                            LanggananModel.paket_layanan
                        ),
                        selectinload(PelangganModel.data_teknis),
                    )
                )
            )
            invoices_to_process = (
                (await db.execute(unprocessed_stmt)).scalars().unique().all()
            )

            processed_count = 0
            if invoices_to_process:
                logger.warning(
                    f"[VERIFY] Menemukan {len(invoices_to_process)} pembayaran terlewat. Memproses..."
                )
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
            logger.error(
                f"[FAIL] Scheduler 'job_verify_payments' failed. Details:\n{error_details}"
            )


async def job_retry_mikrotik_syncs():
    log_scheduler_event(logger, "job_retry_mikrotik_syncs", "started")
    total_retried = 0
    async with SessionLocal() as db:
        try:
            # Cari semua data teknis yang sinkronisasinya tertunda
            stmt = (
                select(DataTeknisModel)
                .where(DataTeknisModel.mikrotik_sync_pending == True)
                .options(
                    selectinload(DataTeknisModel.pelanggan).selectinload(
                        PelangganModel.langganan
                    )
                )
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
                    await mikrotik_service.trigger_mikrotik_update(
                        db, langganan, data_teknis, data_teknis.id_pelanggan
                    )

                    # Jika berhasil, set flag kembali ke False
                    data_teknis.mikrotik_sync_pending = False
                    db.add(data_teknis)
                    logger.info(
                        f"Successfully synced pending update for Data Teknis ID: {data_teknis.id}"
                    )
                    total_retried += 1
                except Exception as e:
                    # Jika masih gagal, biarkan flag tetap True dan catat error
                    logger.error(
                        f"Still failing to sync Mikrotik for Data Teknis ID {data_teknis.id}: {e}"
                    )

            await db.commit()
            log_scheduler_event(
                logger,
                "job_retry_mikrotik_syncs",
                "completed",
                f"Successfully retried {total_retried} syncs.",
            )
        except Exception as e:
            await db.rollback()
            logger.error(
                f"[FAIL] Scheduler 'job_retry_mikrotik_syncs' encountered an error: {traceback.format_exc()}"
            )
