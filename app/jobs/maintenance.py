# app/jobs/maintenance.py
import logging
import traceback
from datetime import datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal as SessionType
from ..logging_config import log_scheduler_event
from ..models import (
    Invoice as InvoiceModel, 
    Pelanggan as PelangganModel, 
    DataTeknis as DataTeknisModel,
    Langganan as LanggananModel
)
from ..routers.invoice import _process_successful_payment
from ..services import xendit_service, mikrotik_service

logger = logging.getLogger("app.jobs.maintenance")

async def job_verify_payments() -> None:
    log_scheduler_event(logger, "job_verify_payments", "started")
    async with SessionType() as db:
        try:
            paid_invoice_ids = await xendit_service.get_paid_invoice_ids_since(days=3)
            if not paid_invoice_ids:
                log_scheduler_event(logger, "job_verify_payments", "completed", "No new payments.")
                return

            unprocessed_stmt = (
                select(InvoiceModel)
                .where(InvoiceModel.xendit_external_id.in_(paid_invoice_ids), InvoiceModel.status_invoice != "Lunas")
                .options(selectinload(InvoiceModel.pelanggan).options(
                    selectinload(PelangganModel.harga_layanan),
                    selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                    selectinload(PelangganModel.data_teknis),
                ))
            )
            invoices = (await db.execute(unprocessed_stmt)).scalars().unique().all()
            for invoice in invoices:
                await _process_successful_payment(db, invoice)
            
            await db.commit()
            log_scheduler_event(logger, "job_verify_payments", "completed", f"Synced {len(invoices)} payments.")
        except Exception as e:
            logger.error(f"Error in job_verify_payments: {e}")
            await db.rollback()

async def job_retry_mikrotik_syncs() -> None:
    log_scheduler_event(logger, "job_retry_mikrotik_syncs", "started")
    async with SessionType() as db:
        try:
            stmt = (
                select(DataTeknisModel)
                .where(DataTeknisModel.mikrotik_sync_pending == True)
                .options(selectinload(DataTeknisModel.pelanggan).selectinload(PelangganModel.langganan))
            )
            pending_syncs = (await db.execute(stmt)).scalars().all()
            for data_teknis in pending_syncs:
                try:
                    langganan = data_teknis.pelanggan.langganan[0]
                    await mikrotik_service.trigger_mikrotik_update(db, langganan, data_teknis, data_teknis.id_pelanggan)
                    data_teknis.mikrotik_sync_pending = False
                    db.add(data_teknis)
                except Exception as e:
                    logger.error(f"Sync fail for {data_teknis.id}: {e}")
            await db.commit()
        except Exception as e:
            await db.rollback()
    log_scheduler_event(logger, "job_retry_mikrotik_syncs", "completed")

async def job_archive_historical_invoices() -> None:
    # Mengimpor fungsi arsip eksternal jika ada
    try:
        from ..archive_invoice_job import archive_old_invoices
        log_scheduler_event(logger, "job_archive_historical_invoices", "started")
        # archive_old_invoices() logic here
    except ImportError:
        logger.warning("archive_invoice_job module not found.")
    log_scheduler_event(logger, "job_archive_historical_invoices", "completed")
