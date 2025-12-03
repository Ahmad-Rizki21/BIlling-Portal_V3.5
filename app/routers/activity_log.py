from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
import re

from ..database import get_db
from ..models.activity_log import ActivityLog as ActivityLogModel
from ..models.user import User as UserModel
from pydantic import BaseModel, ConfigDict
from datetime import datetime, date

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
    search: Optional[str] = Query(None, description="Search in action or details"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """Mengambil daftar log aktivitas dengan paginasi dan filter."""

    # Build base query with filters
    conditions = []

    # Search filter - search in action and details
    if search:
        search_pattern = f"%{search.lower()}%"
        conditions.append(
            or_(
                func.lower(ActivityLogModel.action).ilike(search_pattern),
                func.lower(ActivityLogModel.details).ilike(search_pattern)
            )
        )

    # User filter
    if user_id:
        conditions.append(ActivityLogModel.user_id == user_id)

    # Action filter
    if action:
        conditions.append(ActivityLogModel.action.ilike(f"{action}%"))

    # Date range filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            conditions.append(func.date(ActivityLogModel.timestamp) >= from_date)
        except ValueError:
            pass  # Invalid date format, ignore filter

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            conditions.append(func.date(ActivityLogModel.timestamp) <= to_date)
        except ValueError:
            pass  # Invalid date format, ignore filter

    # Build total query with conditions
    total_query = select(ActivityLogModel)
    if conditions:
        total_query = total_query.where(and_(*conditions))

    total_result = await db.execute(select(func.count()).select_from(total_query.subquery()))
    total = total_result.scalar_one()

    # Build items query with conditions
    items_query = (
        select(ActivityLogModel)
        .options(selectinload(ActivityLogModel.user))
    )

    if conditions:
        items_query = items_query.where(and_(*conditions))

    items_query = (
        items_query
        .order_by(ActivityLogModel.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(items_query)
    items = result.scalars().all()

    return {"items": items, "total": total}
