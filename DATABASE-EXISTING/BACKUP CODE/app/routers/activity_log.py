from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.activity_log import ActivityLog as ActivityLogModel
from ..models.user import User as UserModel

router = APIRouter(
    prefix="/activity-logs",
    tags=["Activity Logs"],
    responses={404: {"description": "Not found"}},
)

# --- Schemas ---
class UserSimple(BaseModel):
    id: int
    name: str
    email: str

class ActivityLogSchema(BaseModel):
    id: int
    user: UserSimple
    timestamp: datetime
    action: str
    details: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedActivityLogResponse(BaseModel):
    items: List[ActivityLogSchema]
    total: int

# --- Endpoint ---
@router.get("/", response_model=PaginatedActivityLogResponse)
async def get_activity_logs(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """Mengambil daftar log aktivitas dengan paginasi."""
    
    # Query untuk mengambil total item
    total_query = select(ActivityLogModel)
    total_result = await db.execute(select(func.count()).select_from(total_query.subquery()))
    total = total_result.scalar_one()

    # Query untuk mengambil item dengan paginasi dan relasi
    items_query = (
        select(ActivityLogModel)
        .options(selectinload(ActivityLogModel.user))
        .order_by(ActivityLogModel.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(items_query)
    items = result.scalars().all()
    
    return {"items": items, "total": total}