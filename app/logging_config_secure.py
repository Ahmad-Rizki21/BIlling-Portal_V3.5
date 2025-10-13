"""
Secure logging configuration with sensitive data filtering
"""

import logging
import logging.config
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# Import our custom logging utilities
from .logging_utils import SensitiveDataFilter

# --- ASCII Art Banner (Windows Compatible) ---
ARTACOM_ASCII = """
+====================================================================+
|                                                                    |
|    █████╗ ██████╗ ████████╗ █████╗  ██████╗ ██████╗ ███╗   ███     |
|   ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔═══██╗████╗ ████     |
|   ███████║██████╔╝   ██║   ███████║██║     ██║   ██║██╔████╔██     |
|   ██╔══██║██╔══██╗   ██║   ██╔══██║██║     ██║   ██║██║╚██╔╝██     |
|   ██║  ██║██║  ██║   ██║   ██║  ██║╚██████╗╚██████╔╝██║ ╚═╝ ██     |
|   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═     |
|                                                                    |
|                      << API SYSTEM >>                              |
|               FTTH Billing Management Platform                     |
|                << CREATED BY AHMAD RIZKI >>                        |
+====================================================================+
"""

STARTUP_BANNER = """
+------------------------------------------------------------------+
|  >> SYSTEM STATUS: INITIALIZING...                               |
|  >> Startup Time: {timestamp}                                    |
|  >> Log Directory: {log_path}                                    |
|  >> Environment: Production Ready                                |
|  >> INSTAGRAM: amad.dyk                                          |
+------------------------------------------------------------------+
"""


# Detect if we can use Unicode characters
def can_use_unicode() -> bool:
    """Check if terminal supports Unicode characters"""
    try:
        # Check if we're in Windows cmd
        if platform.system() == "Windows":
            # Try to detect if we're in a modern terminal
            if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
                return True
            return False
        return True
    except:
        return False


USE_UNICODE = can_use_unicode()

# --- Enhanced Helper Functions for Structured Logging ---


def log_scheduler_event(logger: logging.Logger, job_name: str, status: str, details: str = "") -> None:
    """Enhanced scheduler logging with better formatting"""
    if USE_UNICODE:
        status_icons = {
            "started": "🟢 [START]",
            "completed": "✅ [DONE]",
            "failed": "🔴 [FAIL]",
            "skipped": "⚠️  [SKIP]",
        }
    else:
        status_icons = {
            "started": "[START]",
            "completed": "[DONE]",
            "failed": "[FAIL]",
            "skipped": "[SKIP]",
        }

    icon = status_icons.get(status, "[INFO]")
    message = f"{icon} Scheduler '{job_name}' {status}"
    if details:
        message += f" | Details: {details}"

    if status == "failed":
        logger.error(message)
    elif status == "completed":
        logger.info(message)
    else:
        logger.info(message)


def log_mikrotik_operation(logger: logging.Logger, operation: str, customer_id: str, status: str, details: str = "") -> None:
    """Enhanced MikroTik operation logging"""
    if USE_UNICODE:
        status_icons = {
            "success": "✅ [OK]",
            "failed": "❌ [FAIL]",
            "info": "ℹ️  [INFO]",
            "connecting": "🔄 [CONN]",
            "timeout": "⏰ [TIMEOUT]",
        }
    else:
        status_icons = {
            "success": "[OK]",
            "failed": "[FAIL]",
            "info": "[INFO]",
            "connecting": "[CONN]",
            "timeout": "[TIMEOUT]",
        }

    icon = status_icons.get(status, "[OP]")
    message = f"{icon} MikroTik | {operation} for Customer: '{customer_id}'"
    if details:
        message += f" | {details}"

    if status == "failed" or status == "timeout":
        logger.error(message)
    elif status == "success":
        logger.info(message)
    else:
        logger.info(message)


def log_payment_event(logger, event: str, invoice_id: str, amount: str = "", details: str = ""):
    """Enhanced payment event logging"""
    if USE_UNICODE:
        event_icons = {
            "created": "📄 [CREATED]",
            "paid": "💰 [PAID]",
            "failed": "❌ [FAILED]",
            "pending": "⏳ [PENDING]",
            "cancelled": "🚫 [CANCELLED]",
            "refunded": "↩️  [REFUND]",
        }
    else:
        event_icons = {
            "created": "[CREATED]",
            "paid": "[PAID]",
            "failed": "[FAILED]",
            "pending": "[PENDING]",
            "cancelled": "[CANCELLED]",
            "refunded": "[REFUND]",
        }

    icon = event_icons.get(event.lower(), "[PAYMENT]")
    message = f"{icon} Invoice: {invoice_id}"
    if amount:
        message += f" | Amount: {amount}"
    if details:
        message += f" | {details}"

    if event.lower() in ["failed", "cancelled"]:
        logger.error(message)
    else:
        logger.info(message)


def log_database_event(logger, operation: str, table: str, status: str, details: str = ""):
    """Database operation logging"""
    if USE_UNICODE:
        status_icons = {
            "success": "✅ [OK]",
            "failed": "❌ [FAIL]",
            "connecting": "🔄 [CONN]",
            "migrating": "🔄 [MIGRATE]",
        }
    else:
        status_icons = {
            "success": "[OK]",
            "failed": "[FAIL]",
            "connecting": "[CONN]",
            "migrating": "[MIGRATE]",
        }

    icon = status_icons.get(status, "[DB]")
    message = f"{icon} Database | {operation} on '{table}'"
    if details:
        message += f" | {details}"

    if status == "failed":
        logger.error(message)
    else:
        logger.info(message)


def log_api_request(logger, method: str, endpoint: str, status_code: int, duration: float = 0.0):
    """API request logging"""
    if USE_UNICODE:
        status_icon = "✅" if 200 <= status_code < 300 else "⚠️" if 300 <= status_code < 400 else "❌"
    else:
        status_icon = "[OK]" if 200 <= status_code < 300 else "[WARN]" if 300 <= status_code < 400 else "[ERR]"

    message = f"{status_icon} [{method}] {endpoint} -> {status_code}"
    if duration:
        message += f" | {duration:.2f}ms"

    if status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)


# --- Enhanced Colored Formatter ---


class EnhancedColoredFormatter(logging.Formatter):
    """Enhanced formatter with better colors and compatibility"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[92m",  # Bright Green
        "WARNING": "\033[93m",  # Bright Yellow
        "ERROR": "\033[91m",  # Bright Red
        "CRITICAL": "\033[95m",  # Bright Magenta
        "RESET": "\033[0m",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Disable colors on Windows cmd if not supported
        if platform.system() == "Windows" and not USE_UNICODE:
            self.use_colors = False
        else:
            self.use_colors = True

    def format(self, record):
        if self.use_colors:
            color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
            reset = self.COLORS["RESET"]
            record.levelname = f"{color}{record.levelname:<8}{reset}"
        else:
            record.levelname = f"{record.levelname:<8}"

        # Clean module name
        module_name = record.name.replace("app.", "").upper()
        if len(module_name) > 12:
            module_name = module_name[:9] + "..."
        record.name = f"{module_name:<12}"

        return super().format(record)


class SecureFileFormatter(logging.Formatter):
    """Secure formatter that works with our sensitive data filter"""

    def format(self, record):
        record.name = record.name.replace("app.", "").upper()
        return super().format(record)


# --- Core Logging Setup ---


def setup_secure_logging():
    """Enhanced logging setup with sensitive data filtering"""

    # Create log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Print ASCII Art Banner (safe for all terminals)
    print(ARTACOM_ASCII)

    # Determine separator character
    separator = "|" if not USE_UNICODE else "│"

    # Create sensitive data filter
    sensitive_filter = SensitiveDataFilter()

    # Configuration dictionary
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": EnhancedColoredFormatter,
                "format": f"%(asctime)s {separator} %(name)s {separator} %(levelname)s {separator} %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "detailed": {
                "()": SecureFileFormatter,
                "format": f"%(asctime)s {separator} %(name)-15s {separator} %(levelname)-8s {separator} %(funcName)-20s {separator} %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "()": SecureFileFormatter,
                "format": f"%(asctime)s {separator} %(levelname)-8s {separator} %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "colored",
                "stream": sys.stdout,
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_dir / "app.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": log_dir / "errors.log",
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8",
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": log_dir / "access.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console", "file_app", "file_error"],
                "level": "INFO",
                "propagate": False,
            },
            "app.api": {
                "handlers": ["console", "file_access"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file_app"],
                "level": "WARNING",
                "propagate": False,
            },
            "apscheduler": {
                "handlers": ["console", "file_app"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file_app"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["file_access"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {"level": "INFO", "handlers": ["console", "file_app", "file_error"]},
    }

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Get main logger
    logger = logging.getLogger("app.main")

    # Add sensitive data filter to all handlers
    for handler in logger.handlers:
        handler.addFilter(sensitive_filter)

    # Add sensitive data filter to all other loggers
    app_logger = logging.getLogger("app")
    for handler in app_logger.handlers:
        handler.addFilter(sensitive_filter)

    api_logger = logging.getLogger("app.api")
    for handler in api_logger.handlers:
        handler.addFilter(sensitive_filter)

    middleware_logger = logging.getLogger("app.middleware")
    for handler in middleware_logger.handlers:
        handler.addFilter(sensitive_filter)

    # Print startup banner with dynamic info (safe characters only)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    startup_info = STARTUP_BANNER.format(timestamp=current_time, log_path=str(log_dir.absolute())[:45] + "...")
    print(startup_info)

    # Log startup messages (safe characters only)
    logger.info("=" * 60)
    logger.info(">> SISTEM LOGGING BERHASIL DIINISIALISASI!")
    logger.info(f">> File log disimpan di: {log_dir.absolute()}")
    logger.info(f">> Waktu startup: {current_time}")
    logger.info(">> Semua handler logging aktif dan siap digunakan")
    logger.info("=" * 60)

    return logger


# --- Example Usage Functions ---


def log_system_health(logger):
    """Log system health check"""
    if USE_UNICODE:
        logger.info("💊 System Health Check - All services running normally")
    else:
        logger.info("[HEALTH] System Health Check - All services running normally")


def log_startup_complete(logger):
    """Log application startup completion"""
    if USE_UNICODE:
        logger.info("🚀 APPLICATION STARTUP COMPLETE - Ready to serve requests!")
    else:
        logger.info(">> APPLICATION STARTUP COMPLETE - Ready to serve requests!")


def log_shutdown(logger):
    """Log application shutdown"""
    logger.info(">> Application shutting down gracefully...")
    logger.info(">> ARTACOM API SYSTEM - Goodbye!")


# --- Quick Test Function ---
if __name__ == "__main__":
    # Test the logging setup
    test_logger = setup_secure_logging()

    # Test different log types
    log_scheduler_event(test_logger, "daily_billing", "started", "Processing 150 customers")
    log_mikrotik_operation(
        test_logger,
        "disconnect_user",
        "CUST001",
        "success",
        "User disconnected successfully",
    )
    log_payment_event(test_logger, "paid", "INV-2024-001", "Rp 150,000", "Payment via bank transfer")
    log_database_event(test_logger, "backup", "customers", "success", "1,250 records backed up")
    log_api_request(test_logger, "POST", "/api/v1/customers", 201, 145.5)

    test_logger.debug("Debug message test")
    test_logger.info("Info message test")
    test_logger.warning("Warning message test")
    test_logger.error("Error message test")

    log_startup_complete(test_logger)
