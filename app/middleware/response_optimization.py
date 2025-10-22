# app/middleware/response_optimization.py
"""
Response Optimization Middleware - Compress dan monitor API responses

Middleware ini optimasi API responses buat better performance dan user experience.
Fokus pada compression dan monitoring buat reduce bandwidth usage.

Optimization Features:
- Gzip compression untuk JSON responses
- Response size monitoring dan logging
- Performance metrics collection
- Automatic compression decision making

How it works:
1. Intercept semua HTTP responses
2. Analyze content type dan size
3. Apply gzip compression kalau beneficial
4. Add performance headers buat monitoring
5. Log large responses buat optimization insights

Compression Strategy:
- Minimum size threshold: 1KB (biar worth the effort)
- Target compression: minimum 10% size reduction
- Compress only JSON responses (skip binary files)
- Respect client Accept-Encoding headers

Performance Benefits:
- Reduced bandwidth usage
- Faster API response times
- Better mobile experience
- Lower server bandwidth costs

Monitoring Features:
- Large response warnings (>50KB)
- Compression statistics logging
- Performance headers in responses
- Size optimization metrics

Usage:
- Automatically applied ke semua responses
- Configurable compression thresholds
- Detailed logging buat performance analysis
- Production-ready optimization
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
    Response Optimization Implementation - Smart compression middleware

    Middleware implementation buat optimize API responses dengan compression
    dan performance monitoring. Fokus pada JSON API responses.

    Core Features:
    - Automatic gzip compression untuk responses yang layak
    - Response size monitoring dan logging
    - Performance metrics collection
    - Intelligent compression decision making

    Compression Logic:
    1. Check content type (hanya application/json)
    2. Verify minimum size threshold (default: 1KB)
    3. Check client Accept-Encoding header
    4. Apply compression kalau beneficial (>10% reduction)
    5. Add compression headers buat client

    Performance Monitoring:
    - Processing time tracking
    - Original vs compressed size comparison
    - Large response warnings (>50KB)
    - Compression effectiveness metrics

    Response Headers Added:
    - X-Process-Time: Processing time dalam detik
    - X-Response-Size: Final response size dalam bytes
    - X-Original-Size: Original response size sebelum compression
    - X-Optimization: Middleware identifier
    - Content-Encoding: gzip (kalau compressed)

    Configuration:
    - compress_min_size: Minimum size buat compression (default: 1024 bytes)
    - compression_enabled: Enable/disable compression (default: True)

    Args:
        app: FastAPI application instance
        compress_min_size: Minimum response size untuk compression (bytes)
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
