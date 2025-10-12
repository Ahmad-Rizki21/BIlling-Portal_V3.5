from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.system_log import SystemLog as SystemLogModel
from ..schemas.log import SystemLog as SystemLogSchema

router = APIRouter(prefix="/logs/system", tags=["System Logs"])


@router.get("/", response_model=List[SystemLogSchema])
async def get_system_logs(skip: int = 0, limit: int = 200, db: AsyncSession = Depends(get_db)):
    """Mengambil daftar log sistem, diurutkan dari yang terbaru."""
    query = select(SystemLogModel).order_by(SystemLogModel.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
