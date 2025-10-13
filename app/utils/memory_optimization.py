"""
Memory optimization utilities untuk handling large datasets efficiently.
"""

import asyncio

try:
    import psutil
except ImportError:
    psutil = None
    print("Warning: psutil not installed. Install with: pip install psutil")
import gc
import logging
import tracemalloc
from typing import Any, AsyncGenerator, Callable, Collection, List, Optional, Sequence

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# Memory monitoring configuration
MEMORY_WARNING_THRESHOLD = 80  # Warning at 80% memory usage
MEMORY_CRITICAL_THRESHOLD = 90  # Critical at 90% memory usage
DEFAULT_BATCH_SIZE = 1000
MAX_EXPORT_BATCH_SIZE = 5000


class MemoryMonitor:
    """Monitor memory usage dan log warnings jika needed."""

    def __init__(self):
        if psutil:
            self.process = psutil.Process()
        else:
            self.process = None
        self.snapshot = None

    def start_tracing(self):
        """Start memory tracing."""
        tracemalloc.start()
        self.snapshot = tracemalloc.take_snapshot()

    def get_memory_usage(self) -> dict:
        """Get current memory usage information."""
        memory_info = self.process.memory_info()
        memory_percent = self.process.memory_percent()

        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent_used": memory_percent,
            "available_gb": psutil.virtual_memory().available / 1024 / 1024 / 1024,
            "total_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
        }

    def check_memory_status(self) -> str:
        """Check memory status and return status string."""
        memory_percent = self.process.memory_percent()

        if memory_percent >= MEMORY_CRITICAL_THRESHOLD:
            return "critical"
        elif memory_percent >= MEMORY_WARNING_THRESHOLD:
            return "warning"
        else:
            return "healthy"

    def log_memory_usage(self, operation: str = ""):
        """Log current memory usage."""
        memory_info = self.get_memory_usage()
        status = self.check_memory_status()

        log_message = f"📊 Memory {status}: {memory_info['percent_used']:.1f}% "
        log_message += f"({memory_info['rss_mb']:.1f}MB RSS, "
        log_message += f"{memory_info['available_gb']:.1f}GB available)"

        if operation:
            log_message += f" - {operation}"

        if status == "critical":
            logger.critical(log_message)
        elif status == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        return memory_info

    def get_memory_diff(self) -> Optional[dict]:
        """Get memory difference since last snapshot."""
        if not self.snapshot:
            return None

        current_snapshot = tracemalloc.take_snapshot()
        top_stats = current_snapshot.compare_to(self.snapshot, "lineno")

        total_diff = sum(stat.size_diff for stat in top_stats)
        self.snapshot = current_snapshot

        return {"total_diff_mb": total_diff / 1024 / 1024, "top_stats": top_stats[:10]}  # Top 10 memory allocations


memory_monitor = MemoryMonitor()


async def execute_with_memory_monitor(
    session: AsyncSession, query: Any, operation_name: str = "query", batch_size: int = DEFAULT_BATCH_SIZE
) -> AsyncGenerator[Sequence[Any], Any]:
    """
    Execute query dengan memory monitoring dan streaming results.

    Args:
        session: Database session
        query: SQLAlchemy query
        operation_name: Name for logging
        batch_size: Number of records to process at once

    Yields:
        Batches of results
    """
    memory_monitor.start_tracing()
    initial_memory = memory_monitor.get_memory_usage()

    logger.info(f"🚀 Starting {operation_name} with {initial_memory['rss_mb']:.1f}MB RSS")

    try:
        offset = 0
        while True:
            # Get batch with pagination
            batch_query = query.offset(offset).limit(batch_size)
            result = await session.execute(batch_query)
            batch = result.scalars().all()

            if not batch:
                break

            # Log memory usage for this batch
            current_memory = memory_monitor.get_memory_usage()
            memory_diff = current_memory["rss_mb"] - initial_memory["rss_mb"]

            logger.info(f"📦 Processing batch {offset//batch_size + 1} " f"({len(batch)} records, +{memory_diff:.1f}MB)")

            # Check memory status
            status = memory_monitor.check_memory_status()
            if status == "critical":
                logger.critical(f"🚨 CRITICAL: Memory usage at {current_memory['percent_used']:.1f}%")
                # Force garbage collection
                gc.collect()
                # Reduce batch size for next iteration
                batch_size = max(100, batch_size // 2)
                logger.warning(f"⚠️  Reduced batch size to {batch_size} due to memory pressure")

            yield batch
            offset += len(batch)

            # Small delay to allow memory cleanup
            await asyncio.sleep(0.01)

    except Exception as e:
        logger.error(f"❌ Error in {operation_name}: {e}")
        raise
    finally:
        final_memory = memory_monitor.get_memory_usage()
        memory_diff = final_memory["rss_mb"] - initial_memory["rss_mb"]

        logger.info(
            f"✅ Completed {operation_name}: "
            f"Total memory change: {memory_diff:+.1f}MB "
            f"({final_memory['rss_mb']:.1f}MB RSS)"
        )

        # Get memory allocation details if significant change
        if abs(memory_diff) > 50:  # More than 50MB change
            diff_details = memory_monitor.get_memory_diff()
            if diff_details:
                logger.info(f"🔍 Memory allocation details: {diff_details['total_diff_mb']:.1f}MB change")


def optimize_large_list_comprehension(
    data: List[Any], transform_func: Callable[[Any], Any], batch_size: int = DEFAULT_BATCH_SIZE
) -> List[Any]:
    """
    Optimize large list comprehensions dengan processing berbasis batch.

    Args:
        data: Input data list
        transform_func: Function to transform each item
        batch_size: Number of items to process at once

    Returns:
        Transformed data list
    """
    if len(data) <= batch_size:
        return [transform_func(item) for item in data]

    result = []
    total_items = len(data)

    logger.info(f"🔄 Processing {total_items} items in batches of {batch_size}")

    for i in range(0, total_items, batch_size):
        batch = data[i : i + batch_size]
        batch_result = [transform_func(item) for item in batch]
        result.extend(batch_result)

        # Log progress
        progress = (i + len(batch)) / total_items * 100
        logger.info(f"📊 Progress: {progress:.1f}% ({i + len(batch)}/{total_items} items)")

        # Check memory every few batches
        if i % (batch_size * 5) == 0:
            memory_monitor.log_memory_usage(f"list_comprehension_batch_{i//batch_size}")

            # Force garbage collection if memory is high
            if memory_monitor.check_memory_status() == "critical":
                logger.warning("🗑️  Forcing garbage collection due to memory pressure")
                gc.collect()

    return result


async def create_streaming_csv_response(
    data_generator: AsyncGenerator[List[dict], None], filename: str, headers: Collection[str]
) -> AsyncGenerator[str, None]:
    """
    Create streaming CSV response untuk mengurangi memory usage.

    Args:
        data_generator: Async generator that yields batches of data
        filename: CSV filename
        headers: CSV headers

    Yields:
        CSV content chunks
    """
    import csv
    import io

    # Create CSV header
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    yield output.getvalue()
    output.close()

    # Stream data batches
    async for batch in data_generator:
        output = io.StringIO()
        writer = csv.writer(output)

        for row in batch:
            writer.writerow([row.get(header, "") for header in headers])

        yield output.getvalue()
        output.close()

        # Small delay to allow memory cleanup
        await asyncio.sleep(0.001)


def get_safe_export_limit(requested_limit: int) -> int:
    """
    Get safe export limit berdasarkan available memory.

    Args:
        requested_limit: Requested export limit

    Returns:
        Safe limit based on memory constraints
    """
    memory_status = memory_monitor.check_memory_status()
    memory_info = memory_monitor.get_memory_usage()

    # Adjust limit based on memory status
    if memory_status == "critical":
        safe_limit = min(requested_limit, 1000)  # Very conservative
    elif memory_status == "warning":
        safe_limit = min(requested_limit, 5000)  # Conservative
    else:
        safe_limit = min(requested_limit, MAX_EXPORT_BATCH_SIZE)  # Normal

    logger.info(
        f"📏 Export limit adjusted: {requested_limit} -> {safe_limit} "
        f"(memory: {memory_status}, {memory_info['percent_used']:.1f}% used)"
    )

    return safe_limit


async def force_garbage_collection_if_needed() -> bool:
    """
    Force garbage collection jika memory usage tinggi.

    Returns:
        True if garbage collection was performed
    """
    memory_status = memory_monitor.check_memory_status()

    if memory_status in ["critical", "warning"]:
        logger.warning(f"🗑️  Force garbage collection triggered (memory: {memory_status})")

        before_gc = memory_monitor.get_memory_usage()
        gc.collect()
        await asyncio.sleep(0.1)  # Allow time for GC to complete

        after_gc = memory_monitor.get_memory_usage()
        freed_memory = before_gc["rss_mb"] - after_gc["rss_mb"]

        logger.info(f"✅ Garbage collection freed {freed_memory:.1f}MB")
        return True

    return False
