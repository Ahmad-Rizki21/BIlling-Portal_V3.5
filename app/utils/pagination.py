"""
Pagination utilities for API endpoints to prevent memory issues and improve performance.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters for API endpoints."""

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=10000, description="Maximum 10,000 records per request")


class PaginatedResponse(BaseModel, Generic[T]):
    """Standard paginated response format."""

    data: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    class Config:
        arbitrary_types_allowed = True


async def get_paginated_results(
    db: AsyncSession,
    model: Type[DeclarativeBase],
    skip: int = 0,
    limit: int = 100,
    where_conditions: Optional[List[Any]] = None,
    order_by: Optional[Any] = None,
    include_joins: Optional[List[Any]] = None,
) -> PaginatedResponse[DeclarativeBase]:
    """
    Get paginated results with total count for any model.

    Args:
        db: Database session
        model: SQLAlchemy model class
        skip: Number of records to skip
        limit: Maximum records to return
        where_conditions: List of where conditions
        order_by: Order by clause
        include_joins: List of joinedload options

    Returns:
        PaginatedResponse with data and metadata
    """
    # Build base query
    query = select(model)

    # Add joins if specified
    if include_joins:
        for join_opt in include_joins:
            query = query.options(join_opt)

    # Add where conditions
    if where_conditions:
        for condition in where_conditions:
            query = query.where(condition)

    # Add ordering
    if order_by:
        query = query.order_by(order_by)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query) or 0

    # Apply pagination
    query = query.offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    data = result.scalars().all()

    return PaginatedResponse(data=list(data), total=total, skip=skip, limit=limit, has_more=(skip + limit) < total)


def validate_pagination_params(skip: int, limit: int, max_limit: int = 10000) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.

    Args:
        skip: Raw skip parameter
        limit: Raw limit parameter
        max_limit: Maximum allowed limit

    Returns:
        Tuple of validated (skip, limit)
    """
    skip = max(0, skip)
    limit = max(1, min(limit, max_limit))
    return skip, limit


def get_pagination_headers(skip: int, limit: int, total: int) -> Dict[str, str]:
    """
    Generate pagination headers for response.

    Args:
        skip: Current skip value
        limit: Current limit value
        total: Total number of records

    Returns:
        Dictionary of pagination headers
    """
    return {
        "X-Total-Count": str(total),
        "X-Skip": str(skip),
        "X-Limit": str(limit),
        "X-Has-More": str((skip + limit) < total),
        "Access-Control-Expose-Headers": "X-Total-Count, X-Skip, X-Limit, X-Has-More",
    }
