# app/jobs/billing.py
import logging
import math
import traceback
import re
from datetime import date, datetime, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import AsyncSessionLocal as SessionType
from ..logging_config import log_scheduler_event
from ..models import (
    Invoice as InvoiceModel, 
    Langganan as LanggananModel, 
    Pelanggan as PelangganModel, 
    Diskon as DiskonModel
)
from ..services import xendit_service
from ..services.rate_limiter import create_invoice_with_rate_limit, InvoicePriority
from ..services.invoice_service import InvoiceService
from ..utils.phone_utils import normalize_phone_for_xendit
from ..websocket_manager import manager

logger = logging.getLogger("app.jobs.billing")

async def generate_single_invoice(db: AsyncSession, langganan: LanggananModel) -> bool:
    invoice_service = InvoiceService()
    try:
        await invoice_service.create_invoice(
            db=db,
            langganan_id=langganan.id
        )
        return True
    except Exception as e:
        logger.error(f"⚠️ Gagal generate invoice otomatis untuk langganan {langganan.id}: {e}")
        return False

async def job_generate_invoices() -> None:
    log_scheduler_event(logger, "job_generate_invoices", "started")
    target_due_date = date.today() + timedelta(days=5)
    total_invoices_created = 0
    BATCH_SIZE = 30 

    async with SessionType() as db:
        db.expire_on_commit = False
        try:
            all_ids_stmt = (
                select(LanggananModel.id)
                .where(
                    LanggananModel.tgl_jatuh_tempo >= target_due_date,
                    LanggananModel.tgl_jatuh_tempo < target_due_date + timedelta(days=1),
                    LanggananModel.status == "Aktif",
                )
            )
            all_langganan_ids = (await db.execute(all_ids_stmt)).scalars().all()
        except Exception as e:
            logger.error(f"Gagal ambil data langganan: {e}")
            all_langganan_ids = []

        for batch_start in range(0, len(all_langganan_ids), BATCH_SIZE):
            batch_ids = all_langganan_ids[batch_start:batch_start + BATCH_SIZE]
            try:
                batch_stmt = (
                    select(LanggananModel)
                    .where(LanggananModel.id.in_(batch_ids))
                    .options(
                        selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.harga_layanan),
                        selectinload(LanggananModel.pelanggan).selectinload(PelangganModel.data_teknis),
                        selectinload(LanggananModel.paket_layanan),
                    )
                )
                subscriptions_batch = (await db.execute(batch_stmt)).scalars().unique().all()
                for langganan in subscriptions_batch:
                    if await generate_single_invoice(db, langganan):
                        total_invoices_created += 1
            except Exception as e:
                logger.error(f"Error in batch {batch_start}: {e}")

    log_scheduler_event(logger, "job_generate_invoices", "completed", f"Created {total_invoices_created} invoices.")

async def job_retry_failed_invoices() -> None:
    log_scheduler_event(logger, "job_retry_failed_invoices", "started")
    MAX_RETRY = 3
    BATCH_SIZE = 50
    total_success = 0

    async with SessionType() as db:
        stmt = (
            select(InvoiceModel)
            .where(InvoiceModel.xendit_id.is_(None), InvoiceModel.status_invoice == "Belum Dibayar", InvoiceModel.xendit_retry_count < MAX_RETRY)
            .options(
                selectinload(InvoiceModel.pelanggan).options(
                    selectinload(PelangganModel.harga_layanan),
                    selectinload(PelangganModel.data_teknis),
                    selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan),
                )
            )
        )
        failed_invoices = (await db.execute(stmt)).scalars().unique().all()

        for invoice in failed_invoices:
            try:
                pelanggan = invoice.pelanggan
                paket = pelanggan.langganan[0].paket_layanan if pelanggan.langganan else None
                if not all([pelanggan, paket]): continue

                xendit_response = await create_invoice_with_rate_limit(
                    invoice=invoice,
                    pelanggan=pelanggan,
                    paket=paket,
                    deskripsi_xendit=f"Retry Invoice {invoice.invoice_number}",
                    pajak=0, # Simplified for retry
                    no_telp_xendit=normalize_phone_for_xendit(pelanggan.no_telp),
                    priority=InvoicePriority.NORMAL
                )

                if xendit_response and xendit_response.get("id"):
                    invoice.payment_link = xendit_response.get("invoice_url")
                    invoice.xendit_id = xendit_response.get("id")
                    invoice.xendit_status = "completed"
                    total_success += 1
                
                invoice.xendit_retry_count += 1
                db.add(invoice)
                await db.commit()
            except Exception as e:
                logger.error(f"Retry failed for {invoice.invoice_number}: {e}")
                await db.rollback()

    log_scheduler_event(logger, "job_retry_failed_invoices", "completed", f"Retried {total_success} invoices successfully.")
