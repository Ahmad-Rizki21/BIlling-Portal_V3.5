# Dashboard Specific Logger
# ============================
# Specialized logging for dashboard operations and events

from .logging_enhanced import (
    get_logger,
    log_system_event,
    log_api_request,
    log_database_event,
    log_payment_event,
    log_scheduler_event,
    log_exception,
)
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Get dashboard specific logger
dashboard_logger = get_logger("app.dashboard")


class DashboardLogger:
    """Specialized logger for dashboard operations"""

    def __init__(self):
        self.logger = dashboard_logger

    def log_widget_load(self, widget_name: str, status: str, data_count: int = 0, duration: float = 0):
        """Log widget loading events"""
        icon = "📊" if status == "success" else "⚠️" if status == "warning" else "❌"
        message = f"{icon} Widget '{widget_name}' loaded"

        details = []
        if data_count > 0:
            details.append(f"{data_count} items")
        if duration > 0:
            details.append(f"{duration:.2f}ms")

        if details:
            message += f" ({', '.join(details)})"

        if status == "success":
            self.logger.info(message)
        elif status == "warning":
            self.logger.warning(message)
        else:
            self.logger.error(message)

    def log_chart_render(self, chart_name: str, chart_type: str, data_points: int, render_time: float):
        """Log chart rendering performance"""
        icon = "📈"
        message = f"{icon} Chart '{chart_name}' ({chart_type}) rendered"
        message += f" | {data_points} data points | {render_time:.2f}ms"

        # Performance warning if render time is too high
        if render_time > 1000:  # > 1 second
            self.logger.warning(f"{message} | ⚠️ Slow render!")
        else:
            self.logger.info(message)

    def log_data_fetch(self, endpoint: str, status: str, record_count: int = 0, duration: float = 0):
        """Log data fetching operations"""
        icons = {"success": "✅", "failed": "❌", "cached": "💾", "empty": "📭"}

        icon = icons.get(status, "📄")
        message = f"{icon} Data fetch from '{endpoint}'"

        details = []
        if record_count > 0:
            details.append(f"{record_count} records")
        if duration > 0:
            details.append(f"{duration:.2f}ms")

        if details:
            message += f" | {', '.join(details)}"

        if status == "failed":
            self.logger.error(message)
        else:
            self.logger.info(message)

    def log_user_action(self, action: str, user_id: str, target: str = "", details: str = ""):
        """Log user interactions with dashboard"""
        action_icons = {"view": "👁️", "click": "🖱️", "download": "💾", "filter": "🔍", "refresh": "🔄", "export": "📤"}

        icon = action_icons.get(action, "🎯")
        message = f"{icon} User {action}"

        if user_id:
            message += f" | User: {user_id}"
        if target:
            message += f" | Target: {target}"
        if details:
            message += f" | {details}"

        self.logger.info(message)

    def log_performance_metric(self, metric_name: str, value: float, unit: str = "", threshold: Optional[float] = None):
        """Log performance metrics with threshold warnings"""
        icon = "⚡"
        message = f"{icon} Performance: {metric_name} = {value}{unit}"

        if threshold and value > threshold:
            message += f" | ⚠️ Exceeds threshold ({threshold}{unit})"
            self.logger.warning(message)
        else:
            self.logger.info(message)

    def log_cache_event(self, operation: str, key: str, hit: bool = False, duration: float = 0):
        """Log cache operations"""
        icon = "💾" if hit else "🔄"
        status = "HIT" if hit else "MISS"
        message = f"{icon} Cache {status} | Key: {key}"

        if duration > 0:
            message += f" | {duration:.2f}ms"

        self.logger.info(message)

    def log_real_time_update(self, update_type: str, source: str, affected_widgets: list):
        """Log real-time data updates"""
        icon = "🔄"
        message = f"{icon} Real-time update: {update_type}"

        if source:
            message += f" | Source: {source}"
        if affected_widgets:
            message += f" | Widgets: {', '.join(affected_widgets)}"

        self.logger.info(message)

    def log_error_recovery(self, error_type: str, widget: str, recovery_action: str, success: bool):
        """Log error recovery attempts"""
        icon = "🔧" if success else "⚠️"
        message = f"{icon} Error recovery: {error_type} in '{widget}'"

        if recovery_action:
            message += f" | Action: {recovery_action}"

        if success:
            message += " | ✅ Recovered"
            self.logger.info(message)
        else:
            message += " | ❌ Failed"
            self.logger.warning(message)

    def log_session_metrics(self, session_id: str, metrics: Dict[str, Any]):
        """Log session performance metrics"""
        icon = "📊"
        message = f"{icon} Session {session_id} metrics"

        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                message += f" | {key}: {value}"
            elif isinstance(value, str):
                message += f" | {key}: '{value}'"

        self.logger.info(message)

    def debug_query(self, query_name: str, sql: str, params: Optional[Dict] = None, execution_time: float = 0):
        """Debug SQL queries (only in debug mode)"""
        icon = "🔍"
        message = f"{icon} Query: {query_name}"
        message += f" | Time: {execution_time:.2f}ms"

        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            message += f" | Params: {param_str}"

        # Log full SQL in debug
        self.logger.debug(f"SQL: {sql}")
        self.logger.debug(message)


# --- Convenience Functions ---
def get_dashboard_logger() -> DashboardLogger:
    """Get dashboard logger instance"""
    return DashboardLogger()


# --- Default logger instance ---
dashboard_log = get_dashboard_logger()
