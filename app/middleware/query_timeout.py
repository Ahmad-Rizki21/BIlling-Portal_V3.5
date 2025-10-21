"""
Query timeout middleware untuk mencegah long-running queries.
"""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

from fastapi import HTTPException, Request, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Query timeout configuration
DEFAULT_QUERY_TIMEOUT = 30.0  # 30 seconds default timeout
SLOW_QUERY_THRESHOLD = 5.0  # Log queries slower than 5 seconds


class QueryTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware untuk monitor dan timeout query yang terlalu lama."""

    def __init__(self, app, timeout: float = DEFAULT_QUERY_TIMEOUT):
        super().__init__(app)
        self.timeout = timeout
        self.slow_query_threshold = SLOW_QUERY_THRESHOLD

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            # Log slow requests
            processing_time = time.time() - start_time
            if processing_time > self.slow_query_threshold:
                logger.warning(
                    f"⚠️  SLOW_REQUEST: {request.method} {request.url.path} "
                    f"took {processing_time:.2f}s (threshold: {self.slow_query_threshold}s)"
                )

            return response

        except asyncio.TimeoutError:
            logger.error(f"🚨 REQUEST_TIMEOUT: {request.method} {request.url.path} exceeded {self.timeout}s")
            raise HTTPException(status_code=504, detail=f"Request timeout after {self.timeout} seconds")
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(
                f"❌ REQUEST_ERROR: {request.method} {request.url.path} " f"failed after {processing_time:.2f}s: {str(e)}"
            )
            raise


async def execute_with_timeout(
    session: AsyncSession, query: Any, timeout: float = DEFAULT_QUERY_TIMEOUT, operation_name: str = "query"
) -> Any:
    """
    Execute query dengan timeout monitoring.

    Args:
        session: Database session
        query: SQLAlchemy query to execute
        timeout: Timeout in seconds
        operation_name: Name for logging purposes

    Returns:
        Query result

    Raises:
        asyncio.TimeoutError: If query exceeds timeout
    """
    start_time = time.time()

    try:
        # Execute query with timeout
        result = await asyncio.wait_for(session.execute(query), timeout=timeout)

        execution_time = time.time() - start_time

        # Log slow queries
        if execution_time > SLOW_QUERY_THRESHOLD:
            logger.warning(
                f"⚠️  SLOW_QUERY: {operation_name} took {execution_time:.2f}s " f"(threshold: {SLOW_QUERY_THRESHOLD}s)"
            )

        return result

    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        logger.error(f"🚨 QUERY_TIMEOUT: {operation_name} exceeded {timeout}s " f"(executed for {execution_time:.2f}s)")

        # Try to cancel the query
        try:
            await session.close()
        except:
            pass

        raise HTTPException(status_code=504, detail=f"Database query timeout after {timeout} seconds")


def with_query_timeout(timeout: float = DEFAULT_QUERY_TIMEOUT):
    """
    Decorator untuk menambahkan query timeout ke async functions.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            operation_name = f"{func.__module__}.{func.__name__}"

            try:
                result = await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)

                execution_time = time.time() - start_time

                if execution_time > SLOW_QUERY_THRESHOLD:
                    logger.warning(
                        f"⚠️  SLOW_FUNCTION: {operation_name} took {execution_time:.2f}s "
                        f"(threshold: {SLOW_QUERY_THRESHOLD}s)"
                    )

                return result

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                logger.error(
                    f"🚨 FUNCTION_TIMEOUT: {operation_name} exceeded {timeout}s " f"(executed for {execution_time:.2f}s)"
                )

                raise HTTPException(status_code=504, detail=f"Operation timeout after {timeout} seconds")

        return wrapper

    return decorator


# Database-specific query limits
QUERY_LIMITS = {
    "default": 1000,
    "export": 50000,
    "dashboard": 10000,
    "report": 25000,
    "search": 500,
}


def get_query_limit(operation_type: str = "default") -> int:
    """
    Get query limit berdasarkan tipe operasi.

    Args:
        operation_type: Type of operation (default, export, dashboard, report, search)

    Returns:
        Maximum number of records allowed
    """
    return QUERY_LIMITS.get(operation_type, QUERY_LIMITS["default"])


def validate_query_limit(limit: int, operation_type: str = "default") -> int:
    """
    Validate dan normalize query limit.

    Args:
        limit: Requested limit
        operation_type: Type of operation

    Returns:
        Validated limit
    """
    max_limit = get_query_limit(operation_type)
    return min(max(1, limit), max_limit)
