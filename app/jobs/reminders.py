# app/jobs/reminders.py
import logging
from datetime import date, timedelta
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal as SessionType
from ..logging_config import log_scheduler_event
from ..models import (
    Langganan as LanggananModel, 
    Pelanggan as PelangganModel
)

logger = logging.getLogger("app.jobs.reminders")

async def job_send_payment_reminders() -> None:
    log_scheduler_event(logger, "job_send_payment_reminders", "started")
    target_due_date = date.today() + timedelta(days=3)
    BATCH_SIZE = 100
    offset = 0
    total_reminders = 0

    async with SessionType() as db:
        while True:
            stmt = (
                select(LanggananModel)
                .where(LanggananModel.tgl_jatuh_tempo == target_due_date, LanggananModel.status == "Aktif")
                .options(selectinload(LanggananModel.pelanggan))
                .offset(offset).limit(BATCH_SIZE)
            )
            batch = (await db.execute(stmt)).scalars().unique().all()
            if not batch: break

            for langganan in batch:
                # Logika placeholder kirim WA/Email
                logger.info(f"Reminder sent to {langganan.pelanggan.nama}")
                total_reminders += 1
            offset += BATCH_SIZE

    log_scheduler_event(logger, "job_send_payment_reminders", "completed", f"Sent {total_reminders} reminders.")
