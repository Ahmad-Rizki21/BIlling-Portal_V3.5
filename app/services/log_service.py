from sqlalchemy.ext.asyncio import AsyncSession
from ..models.activity_log import ActivityLog


async def create_activity_log(db: AsyncSession, user_id: int, action: str, details: str | None = None):
    """Membuat dan menyimpan log aktivitas baru."""
    db_log = ActivityLog(user_id=user_id, action=action, details=details)
    db.add(db_log)
    await db.flush()  # Menggunakan flush agar log tersimpan dalam transaksi yang sama
