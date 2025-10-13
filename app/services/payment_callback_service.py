from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import logging
import json

from ..models.payment_callback_log import PaymentCallbackLog

logger = logging.getLogger(__name__)


async def check_duplicate_callback(db: AsyncSession, xendit_id: str, external_id: str, idempotency_key: str = "") -> bool:
    """
    Check if a callback has already been processed based on xendit_id, external_id, or idempotency_key.
    Returns True if duplicate, False if not.
    """
    # Check by idempotency key if provided
    if idempotency_key:
        stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.idempotency_key == idempotency_key)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            logger.info(f"Duplicate callback detected by idempotency_key: {idempotency_key}")
            return True

    # Check by xendit_id
    stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.xendit_id == xendit_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        logger.info(f"Duplicate callback detected by xendit_id: {xendit_id}")
        return True

    # Check by external_id
    stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.external_id == external_id)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        logger.info(f"Duplicate callback detected by external_id: {external_id}")
        return True

    return False


async def log_callback_processing(
    db: AsyncSession, xendit_id: str, external_id: str, status: str, callback_data: dict = {}, idempotency_key: str = ""
) -> bool:
    """
    Log the callback processing to prevent duplicates.
    Returns True if successfully logged, False if already exists (duplicate).
    """
    # First check for duplicates
    if await check_duplicate_callback(db, xendit_id, external_id, idempotency_key):
        return False

    try:
        # Prepare callback data as JSON string
        callback_data_str = json.dumps(callback_data, default=str) if callback_data else None

        # Limit callback_data_str length to fit in database field
        if callback_data_str and len(callback_data_str) > 1000:
            callback_data_str = callback_data_str[:997] + "..."

        # Create log entry
        callback_log = PaymentCallbackLog(
            idempotency_key=idempotency_key,
            xendit_id=xendit_id,
            external_id=external_id,
            status=status,
            callback_data=callback_data_str,
        )
        db.add(callback_log)
        await db.commit()
        logger.info(
            f"Callback logged successfully: xendit_id={xendit_id}, external_id={external_id}, idempotency_key={idempotency_key}"
        )
        return True
    except IntegrityError:
        # If there's an integrity error, it means another process created the same record
        await db.rollback()
        logger.info(f"Callback already processed by another process: xendit_id={xendit_id}, external_id={external_id}")
        return False
    except Exception as e:
        await db.rollback()
        logger.error(f"Error logging callback: {str(e)}")
        raise


async def get_callback_log_by_xendit_id(db: AsyncSession, xendit_id: str) -> PaymentCallbackLog:
    """Get callback log by xendit_id."""
    stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.xendit_id == xendit_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_callback_log_by_external_id(db: AsyncSession, external_id: str) -> PaymentCallbackLog:
    """Get callback log by external_id."""
    stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.external_id == external_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_callback_log_by_idempotency_key(db: AsyncSession, idempotency_key: str) -> PaymentCallbackLog:
    """Get callback log by idempotency_key."""
    stmt = select(PaymentCallbackLog).where(PaymentCallbackLog.idempotency_key == idempotency_key)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
