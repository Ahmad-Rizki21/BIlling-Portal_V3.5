"""
Middleware for API Response Optimization.
Menyediakan response compression, monitoring, dan optimization.
"""

import gzip
import logging
import time
from io import BytesIO
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app.response_optimization")


class ResponseOptimizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware untuk optimasi response API:
    - Response size monitoring
    - JSON response compression
    - Performance tracking
    """

    def __init__(self, app, compress_min_size: int = 1024):
        super().__init__(app)
        self.compress_min_size = compress_min_size
        self.compression_enabled = True

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Get response
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Skip optimization for certain content types
        content_type = response.headers.get("content-type", "")
        if any(skip in content_type.lower() for skip in ["image/", "video/", "application/octet-stream"]):
            return response

        # Only optimize JSON responses
        if "application/json" in content_type:
            response = await self._optimize_json_response(response, request, process_time)

        # Add performance headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["X-Response-Size"] = str(len(response.body) if hasattr(response, "body") else 0)

        return response

    async def _optimize_json_response(self, response: Response, request: Request, process_time: float) -> Response:
        """Optimize JSON responses dengan compression dan monitoring."""
        try:
            # Get response body
            if hasattr(response, "body"):
                body = response.body
            else:
                # For streaming responses, return as-is
                return response

            original_size = len(body)

            # Log response size for monitoring
            if original_size > 50000:  # Log responses > 50KB
                logger.warning(
                    f"Large response detected: {original_size} bytes for {request.url.path} " f"took {process_time:.4f}s"
                )

            # Apply compression if beneficial
            if (
                self.compression_enabled
                and original_size >= self.compress_min_size
                and "gzip" not in request.headers.get("accept-encoding", "")
            ):

                compressed_body = self._compress_data(body)
                compressed_size = len(compressed_body)

                # Only use compression if it reduces size
                if compressed_size < original_size * 0.9:  # At least 10% reduction
                    response.body = compressed_body
                    response.headers["Content-Encoding"] = "gzip"
                    response.headers["Content-Length"] = str(compressed_size)

                    logger.info(
                        f"Compressed response: {original_size} -> {compressed_size} bytes "
                        f"({round((1 - compressed_size/original_size) * 100, 1)}% reduction) "
                        f"for {request.url.path}"
                    )

            # Add optimization headers
            response.headers["X-Original-Size"] = str(original_size)
            response.headers["X-Optimization"] = "response-middleware"

            return response

        except Exception as e:
            logger.error(f"Response optimization failed for {request.url.path}: {e}")
            return response

    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using gzip."""
        buffer = BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", compresslevel=6) as gz_file:
            gz_file.write(data)
        return buffer.getvalue()


class ResponseSizeLogger:
    """Utility untuk logging response size optimization."""

    @staticmethod
    def log_optimization(endpoint: str, original_size: int, optimized_size: int):
        """Log hasil optimasi response."""
        reduction_pct = round((1 - optimized_size / original_size) * 100, 1) if original_size > 0 else 0

        if reduction_pct > 20:
            logger.info(
                f"✅ Great optimization: {endpoint} - "
                f"{original_size} -> {optimized_size} bytes ({reduction_pct}% reduction)"
            )
        elif reduction_pct > 5:
            logger.info(
                f"✓ Good optimization: {endpoint} - " f"{original_size} -> {optimized_size} bytes ({reduction_pct}% reduction)"
            )
        else:
            logger.debug(
                f"Minimal optimization: {endpoint} - "
                f"{original_size} -> {optimized_size} bytes ({reduction_pct}% reduction)"
            )

    @staticmethod
    def log_large_response(endpoint: str, size: int, threshold: int = 50000):
        """Log large responses yang perlu optimasi."""
        if size > threshold:
            logger.warning(f"⚠️  Large response detected: {endpoint} - {size:,} bytes " f"(threshold: {threshold:,} bytes)")
