"""
Rate Limiter Monitoring API
Endpoint untuk monitoring queue status dan retry failed invoices.
"""

from fastapi import APIRouter, Depends, HTTPException
from ..services.rate_limiter import rate_limiter
from ..auth import has_permission
import logging

logger = logging.getLogger("app.routers.rate_limiter_monitor")

router = APIRouter(
    prefix="/rate-limiter",
    tags=["Rate Limiter Monitor"],
    responses={404: {"description": "Not found"}},
)


@router.get("/status")
async def get_queue_status():
    """
    Get current queue status for rate limiter.

    Returns:
    - pending: Number of invoices waiting in queue
    - processing: Number of invoices currently being processed
    - completed: Number of successfully processed invoices
    - failed: Number of failed invoices
    - total_processed: Total number of invoices processed
    - total_failed: Total number of invoices failed
    - is_processing: Whether queue is currently processing
    - estimated_wait_time: Estimated wait time in seconds
    """
    try:
        status = await rate_limiter.get_queue_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting queue status: {str(e)}")


@router.post("/retry-failed")
async def retry_failed_invoices():
    """
    Retry all failed invoices in the queue.

    This endpoint will retry all invoices that failed during processing.
    Useful for recovering from temporary failures or network issues.

    Returns:
    - success: Whether retry operation was initiated
    - message: Description of retry result
    - queue_status: Updated queue status after retry
    """
    try:
        result = await rate_limiter.retry_failed_invoices()
        return {
            "success": True,
            "message": result.get("message", "Retry operation completed"),
            "queue_status": result.get("queue_status", {})
        }
    except Exception as e:
        logger.error(f"Error retrying failed invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrying failed invoices: {str(e)}")


@router.get("/health")
async def health_check():
    """
    Health check endpoint for rate limiter service.

    Returns:
    - status: Service health status
    - uptime: Service uptime information
    - queue_health: Queue processing health
    """
    try:
        status = await rate_limiter.get_queue_status()

        # Determine overall health
        if status["failed"] > 50:  # Too many failed invoices
            health_status = "degraded"
        elif status["pending"] > 100:  # Large queue
            health_status = "stressed"
        elif status["is_processing"]:
            health_status = "processing"
        else:
            health_status = "healthy"

        return {
            "success": True,
            "status": health_status,
            "queue_health": status,
            "timestamp": "2025-01-01"  # Static for now
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e)
        }