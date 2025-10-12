"""
Centralized error handling untuk menghilangkan duplikasi error patterns
"""

import logging
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

logger = logging.getLogger(__name__)


def safe_assign(obj, attr: str, fallback: Any = None) -> Any:
    """Safe assignment dengan fallback"""
    try:
        value = getattr(obj, attr, fallback)
        return value
    except AttributeError:
        return fallback


def safe_extend(list_obj: list, items: list) -> bool:
    """Safe list extension dengan error handling"""
    try:
        if items and hasattr(list_obj, "extend"):
            list_obj.extend(items)
            return True
        return False
    except (AttributeError, TypeError):
        logger.warning(f"Cannot extend {type(list_obj)} - {list_obj}")
        return False


def safe_getattr(obj: Any, attr: str, fallback: Any = None) -> Any:
    """Safe attribute access dengan fallback"""
    try:
        return getattr(obj, attr, fallback)
    except (AttributeError, TypeError):
        return fallback


def safe_get_dict(dict_obj: dict, key: str, fallback: Any = None) -> Any:
    """Safe dict access dengan fallback"""
    try:
        return dict_obj.get(key, fallback)
    except (AttributeError, TypeError):
        return fallback


def handle_error_result(data_type: str, result: Any) -> Optional[Any]:
    """
    Handle error result dengan type checking yang tepat
    """
    if isinstance(result, Exception):
        logger.error(f"Error in {data_type}: {result}")
        return None
    elif result is None:
        logger.warning(f"{data_type} returned None")
        return None
    return result


def handle_task_result(task_name: str, result: Any) -> Optional[Any]:
    """Handle task result dengan proper error handling"""
    if isinstance(result, Exception):
        logger.error(f"Error in {task_name}: {result}")
        return None
    elif result is None:
        logger.info(f"{task_name} returned None")
        return None
    return result


import uuid

# 🛡️ GRACEFUL DEGRADATION UTILITIES
from datetime import datetime


class GracefulError(Exception):
    """Custom exception untuk graceful degradation scenarios."""

    def __init__(self, message: str, fallback_data: Any = None, operation: str = "unknown"):
        super().__init__(message)
        self.fallback_data = fallback_data
        self.operation = operation


async def safe_execute_with_fallback(
    operation_name: str, async_operation, fallback_data: Any, context: Optional[Dict[str, Any]] = None
):
    """
    Execute async operation dengan safe fallback.

    Args:
        operation_name: Name of the operation for logging
        async_operation: Async function to execute
        fallback_data: Data to return if operation fails
        context: Additional context for error tracking

    Returns:
        Result of operation or fallback_data if failed
    """
    try:
        return await async_operation()
    except GracefulError as e:
        logger.warning(f"Graceful degradation in {operation_name}: {e}")
        return e.fallback_data or fallback_data
    except HTTPException:
        # HTTP exceptions should propagate
        raise
    except Exception as e:
        logger.error(
            f"Operation {operation_name} failed, using fallback: {str(e)}",
            exc_info=True,
            extra={"operation": operation_name, "context": context or {}},
        )
        return fallback_data


def create_fallback_dashboard():
    """Create empty dashboard structure for graceful degradation."""
    from ..schemas.dashboard import ChartData, DashboardData, InvoiceSummary, RevenueSummary

    empty_revenue_summary = RevenueSummary(total=0.0, periode="bulan", breakdown=[])  # Empty BrandRevenueItem list

    empty_chart = ChartData(labels=[], data=[])
    empty_invoice_summary = InvoiceSummary(labels=[], total=[], lunas=[], menunggu=[], kadaluarsa=[])

    return DashboardData(
        revenue_summary=empty_revenue_summary,
        stat_cards=[],  # Empty stat cards
        lokasi_chart=empty_chart,
        paket_chart=empty_chart,
        growth_chart=empty_chart,
        invoice_summary_chart=empty_invoice_summary,  # Use correct type
        status_langganan_chart=empty_chart,
        pelanggan_per_alamat_chart=empty_chart,
        loyalitas_pembayaran_chart=empty_chart,
    )


def create_fallback_chart():
    """Create empty chart for graceful degradation."""
    from ..routers.dashboard import ChartData

    return ChartData(labels=[], data=[])


def handle_critical_notification_failure(operation: str, notification_data: Dict[str, Any], error: Exception):
    """
    Handle critical notification failures gracefully.
    Notification failures should not crash the main operation.
    """
    logger.error(
        f"⚠️ {operation} notification failed but main operation succeeded: {str(error)}",
        exc_info=True,
        extra={
            "operation": operation,
            "notification_type": notification_data.get("type", "unknown"),
            "fallback_applied": True,
        },
    )

    # Return success indicator - notification failure is non-critical
    return {"notification_sent": False, "error": str(error), "main_operation_success": True, "graceful_degradation": True}


def log_performance_issue(operation: str, execution_time: float, threshold: float = 2.0):
    """
    Log performance issues for monitoring.
    """
    if execution_time > threshold:
        logger.warning(
            f"⚠️ Performance issue in {operation}: {execution_time:.2f}s (threshold: {threshold}s)",
            extra={
                "operation": operation,
                "execution_time": execution_time,
                "threshold": threshold,
                "performance_issue": True,
            },
        )


class ErrorTracker:
    """Track errors for monitoring and debugging."""

    def __init__(self):
        self.error_counts = {}
        self.error_details = {}

    def track_error(self, operation: str, error: Exception, context: Optional[Dict] = None):
        """Track error occurrence for monitoring."""
        error_key = f"{operation}:{type(error).__name__}"

        # Increment error count
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

        # Store error details
        self.error_details[error_key] = {
            "operation": operation,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "count": self.error_counts[error_key],
            "last_occurrence": datetime.now().isoformat(),
            "context": context or {},
        }

        # Log error tracking
        logger.error(
            f"Error tracked: {error_key} (count: {self.error_counts[error_key]})",
            extra={"error_tracking": self.error_details[error_key]},
        )

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors."""
        return {
            "total_errors": sum(self.error_counts.values()),
            "unique_errors": len(self.error_counts),
            "error_details": self.error_details,
        }


# Global error tracker instance
error_tracker = ErrorTracker()
