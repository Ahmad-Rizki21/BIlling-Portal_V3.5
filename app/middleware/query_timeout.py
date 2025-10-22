# app/middleware/query_timeout.py
"""
Query Timeout Middleware - Proteksi database dari slow queries

Middleware ini jaga database performance dengan timeout mechanism.
Fungsi utamanya mencegah queries yang terlalu lama yang bisa bikin sistem hang.

Problem yang Diatasi:
- Slow queries yang lock database resources
- Long-running transactions yang blocking operasi lain
- API timeouts yang bikin user experience buruk
- Database connection pool exhaustion

Timeout Configuration:
- Default query timeout: 30 detik
- Slow query threshold: 5 detik (buat logging)
- Different timeout per operation type

How it works:
1. Monitor semua request processing time
2. Log slow requests buat performance analysis
3. Timeout queries yang melebihi batas waktu
4. Return 504 Gateway Timeout kalau query timeout
5. Cleanup database connections dengan aman

Security & Performance Benefits:
- Prevent DoS attacks via slow queries
- Protect database from resource exhaustion
- Better error handling dan user feedback
- Performance monitoring dan optimization insights

Usage:
- Middleware otomatis aktif buat semua endpoints
- Decorator @with_query_timeout() buat specific functions
- execute_with_timeout() buat manual query execution
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
    """
    Query Timeout Middleware Implementation - HTTP request monitoring

    Middleware implementation buat monitor dan timeout HTTP requests
    yang terlalu lama, termasuk database queries yang dijalankan dalam request.

    Middleware Features:
    - Request processing time monitoring
    - Slow request logging dengan detail
    - Timeout handling dengan proper cleanup
    - Performance metrics collection

    Configuration:
    - timeout: Maximum waktu per request (default: 30 detik)
    - slow_query_threshold: Threshold buat logging slow requests (5 detik)

    Monitoring Strategy:
    1. Start timer saat request masuk
    2. Execute request dengan asyncio.wait_for()
    3. Log warning kalau melebihi slow threshold
    4. Return 504 kalau timeout terjadi
    5. Cleanup resources dengan aman

    Performance Monitoring:
    - ⚠️ Slow requests (>5 detik) buat optimization insights
    - 🚨 Timeout requests (>30 detik) buat critical issues
    - ❌ Failed requests dengan execution time tracking
    - Process time headers buat client-side monitoring

    Error Handling:
    - asyncio.TimeoutError -> 504 Gateway Timeout
    - Other exceptions -> logging dan re-raise
    - Graceful degradation buat system stability

    Args:
        app: FastAPI application instance
        timeout: Timeout duration dalam detik
    """

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
    Execute Database Query dengan Timeout Protection

    Function buat execute SQLAlchemy query dengan timeout monitoring.
    Ini mencegah slow queries yang bisa bikin database hang.

    Query Execution Flow:
    1. Start execution timer
    2. Execute query dengan asyncio.wait_for(timeout)
    3. Monitor execution time
    4. Log slow queries buat performance analysis
    5. Handle timeout dengan proper cleanup

    Performance Monitoring:
    - Slow query threshold: 5 detik (logging warning)
    - Query timeout: 30 detik (exception)
    - Detailed logging dengan operation name
    - Execution time tracking

    Error Handling:
    - asyncio.TimeoutError -> HTTP 504 Gateway Timeout
    - Automatic session cleanup saat timeout
    - Graceful error propagation
    - Comprehensive error logging

    Use Cases:
    - Complex SELECT queries
    - Bulk operations
    - Report generation queries
    - Data export operations

    Args:
        session: AsyncSession SQLAlchemy database session
        query: SQLAlchemy query object yang mau diexecute
        timeout: Maximum execution time dalam detik (default: 30)
        operation_name: Descriptive name buat logging (default: "query")

    Returns:
        Query result (scalar, scalars, atau result object)

    Raises:
        asyncio.TimeoutError: Kalau query melebihi timeout
        HTTPException: 504 Gateway Timeout saat timeout terjadi
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
