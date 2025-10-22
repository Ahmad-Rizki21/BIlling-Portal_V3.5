# app/utils/pagination.py
"""
Pagination utilities buat API endpoints buat prevent memory issues dan improve performance.
Module ini handle pagination dengan standar yang konsisten di seluruh aplikasi.

Features:
- Standard pagination parameters (skip, limit)
- Paginated response format
- Total count calculation
- Performance optimization
- Query builder integration
- Pagination headers generation

Performance benefits:
- Prevent loading entire database tables
- Memory efficient queries
- Consistent response times
- Scalable pagination
- Optimized COUNT queries

Usage in API endpoints:
    @router.get("/customers")
    async def get_customers(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
    ):
        result = await get_paginated_results(
            db, Customer, skip=skip, limit=limit
        )
        return result

Response format:
    {
        "data": [...],
        "total": 1250,
        "skip": 0,
        "limit": 100,
        "has_more": true
    }
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Standard pagination parameters buat API endpoints.
    Validasi input pagination dengan reasonable limits.

    Attributes:
        skip: Number of records to skip (offset)
        limit: Maximum records per request

    Validation:
        - skip: Minimum 0, tidak ada maximum
        - limit: Minimum 1, Maximum 10,000 (prevent overload)

    Usage:
        @router.get("/users")
        async def get_users(
            pagination: PaginationParams = Depends()
        ):
            result = await get_paginated_results(
                db, User, skip=pagination.skip, limit=pagination.limit
            )
            return result

    Performance considerations:
        - Limit 10,000 buat prevent server overload
        - Default limit 100 buat reasonable performance
        - Skip 0 berarti mulai dari record pertama
        - Large limit bisa cause memory issues
    """

    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=100, ge=1, le=10000, description="Maximum 10,000 records per request")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard paginated response format buat consistency.
    Generic class yang bisa dipake buat semua model types.

    Attributes:
        data: List of records (dari specific model)
        total: Total number of records di database
        skip: Current offset (berapa records yang di-skip)
        limit: Current limit (berapa records per request)
        has_more: True kalau masih ada records di halaman berikutnya

    Response example:
        {
            "data": [
                {"id": 1, "name": "Customer 1"},
                {"id": 2, "name": "Customer 2"}
            ],
            "total": 150,
            "skip": 0,
            "limit": 100,
            "has_more": true
        }

    Usage in API:
        return PaginatedResponse(
            data=customers,
            total=total_customers,
            skip=skip,
            limit=limit,
            has_more=(skip + limit) < total_customers
        )

    Frontend integration:
        // Load next page
        if (response.has_more) {
            loadMore(response.skip + response.limit);
        }

        // Calculate total pages
        totalPages = Math.ceil(response.total / response.limit);
    """

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
