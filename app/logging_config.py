# app/logging_config.py
"""
Comprehensive logging configuration untuk Artacom FTTH Billing system.
Module ini handle semua kebutuhan logging dengan features yang lengkap.

Features:
- Multi-level logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Multiple output destinations (console, files)
- Rotating log files buat manage size
- Enhanced colored formatter buat console
- Unicode/ASCII compatibility (Windows friendly)
- Structured logging functions buat consistency
- Sensitive data filtering
- Module-specific log routing

Log files generated:
- logs/app.log (Main application log, 10MB, 5 backups)
- logs/errors.log (Errors only, 5MB, 3 backups)
- logs/access.log (API access log, 10MB, 5 backups)

Usage:
    from app.logging_config import setup_logging
    logger = setup_logging()

    # Atau pake structured logging functions
    from app.logging_config import log_scheduler_event, log_payment_event
    log_scheduler_event(logger, "job_name", "started", "details")
"""

import logging
import logging.config
import os
import platform
import sys
from datetime import datetime
from pathlib import Path

# Import our custom logging utilities
try:
    from .logging_utils import SensitiveDataFilter  # type: ignore

    # If import is successful, SensitiveDataFilter is already defined
except ImportError:
    # Fallback if logging_utils.py doesn't exist
    class FallbackSensitiveDataFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return True

    SensitiveDataFilter = FallbackSensitiveDataFilter  # type: ignore


# --- ASCII Art Banner (Windows Compatible) ---
ARTACOM_ASCII = """
+===============================================================+
|                                                               |
|    █████╗ ██████╗ ████████╗ █████╗  ██████╗ ██████╗ ███╗   ███|
|   ██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██╔═══██╗████╗ ████|
|   ███████║██████╔╝   ██║   ███████║██║     ██║   ██║██╔████╔██|
|   ██╔══██║██╔══██╗   ██║   ██╔══██║██║     ██║   ██║██║╚██╔╝██|
|   ██║  ██║██║  ██║   ██║   ██║  ██║╚██████╗╚██████╔╝██║ ╚═╝ ██|
|   ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝     ╚═|
|                                                               |
|                      << API SYSTEM >>                         |
|               FTTH Billing Management Platform                |
|                                                               |
+===============================================================+
"""

STARTUP_BANNER = """
+-------------------------------------------------------------+
|  >> SYSTEM STATUS: INITIALIZING...                          |
|  >> Startup Time: {timestamp}                               |
|  >> Log Directory: {log_path}                               |
|  >> Environment: Production Ready                           |
+-------------------------------------------------------------+
"""


def can_use_unicode() -> bool:
    """
    Detect terminal support buat Unicode characters dan emojis.
    Fungsinya buat ensure compatibility cross-platform.

    Returns:
        True kalau terminal support Unicode, False kalau harus pake ASCII

    Detection logic:
    - Windows cmd/PowerShell: cek modern terminal indicators
    - WSL (Windows Subsystem for Linux): Unicode supported
    - Linux/macOS: Default Unicode support
    - Modern terminals (Windows Terminal, VS Code): Unicode supported

    Environment variables checked:
    - WT_SESSION: Windows Terminal indicator
    - TERM_PROGRAM: VS Code terminal indicator
    - TERM: Unix terminal type

    Usage:
        if can_use_unicode():
            print("✅ Success!")
        else:
            print("[OK] Success!")

    Note:
    - Fallback ke ASCII kalau tidak yakin
    - Prevent garbled text output
    - Cross-platform compatibility
    """
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
    """
    Structured logging function buat scheduler/job events.
    Standardize format buat semua scheduler logging.

    Args:
        logger: Logger instance yang mau dipake
        job_name: Nama job/scheduler (misal: "daily_billing")
        status: Job status ("started", "completed", "failed", "skipped")
        details: Additional information (optional)

    Status icons:
    - 🟢 [START] = Job dimulai
    - ✅ [DONE] = Job selesai berhasil
    - 🔴 [FAIL] = Job gagal (error)
    - ⚠️ [SKIP] = Job dilewati (misal: tidak ada data)

    Usage examples:
        log_scheduler_event(logger, "daily_billing", "started", "Processing 150 customers")
        log_scheduler_event(logger, "payment_reminder", "completed", "Sent 50 reminders")
        log_scheduler_event(logger, "invoice_generation", "failed", "Database connection error")

    Log level mapping:
    - failed -> ERROR
    - completed -> INFO
    - started/skipped -> INFO

    Note:
    - Auto Unicode/ASCII adaptation
    - Consistent format across all scheduler jobs
    - Easy parsing buat monitoring tools
    """
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


def log_payment_event(logger: logging.Logger, event: str, invoice_id: str, amount: str = "", details: str = "") -> None:
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


def log_database_event(logger: logging.Logger, operation: str, table: str, status: str, details: str = "") -> None:
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


def log_api_request(
    logger: logging.Logger, method: str, endpoint: str, status_code: int, duration: float | None = None
) -> None:
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # Disable colors on Windows cmd if not supported
        if platform.system() == "Windows" and not USE_UNICODE:
            self.use_colors = False
        else:
            self.use_colors = True

    def format(self, record: logging.LogRecord) -> str:
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


class FileFormatter(logging.Formatter):
    """Clean formatter for file output without colors"""

    def format(self, record: logging.LogRecord) -> str:
        record.name = record.name.replace("app.", "").upper()
        return super().format(record)


# --- Core Logging Setup ---


def setup_logging() -> logging.Logger:
    """
    Main function buat setup comprehensive logging system.
    Initialize semua log handlers, formatters, dan konfigurasi.

    Returns:
        Main logger instance (app.main)

    Setup process:
    1. Create logs directory kalau belum ada
    2. Print ASCII art banner (cross-platform compatible)
    3. Setup logging configuration dictionary
    4. Initialize multiple handlers (console + files)
    5. Configure module-specific loggers
    6. Apply sensitive data filters
    7. Print startup information

    Log file configuration:
    - app.log: Debug level, detailed format, 10MB rotation
    - errors.log: Error level only, 5MB rotation
    - access.log: API access, simple format, 10MB rotation

    Handler features:
    - RotatingFileHandler: Automatic log rotation
    - UTF-8 encoding: Support Unicode characters
    - Sensitive data filtering: Hide passwords/API keys
    - Cross-platform compatibility: Windows/Linux/macOS

    Module loggers:
    - app.*: Main application modules
    - sqlalchemy.engine: Database queries (WARNING+)
    - apscheduler: Job scheduling
    - uvicorn: Web server

    Usage:
        logger = setup_logging()
        logger.info("Application started successfully")

    Note:
    - Must dipanggil sekali di application startup
    - Creates log directory otomatis
    - Handles Unicode encoding errors gracefully
    """

    # Create log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Print ASCII Art Banner (safe for all terminals)
    try:
        print(ARTACOM_ASCII)
    except UnicodeEncodeError:
        # Fallback for Windows cmd without UTF-8 support
        print("=" * 65)
        print("  ARTACOM FTTH BILLING API SYSTEM")
        print("  FTTH Billing Management Platform")
        print("=" * 65)

    # Determine separator character
    separator = "|" if not USE_UNICODE else "│"

    # Configuration dictionary
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": EnhancedColoredFormatter,
                "format": f"%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "()": FileFormatter,
                "format": f"%(asctime)s | %(name)-15s | %(levelname)-8s | %(funcName)-20s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "()": FileFormatter,
                "format": f"%(asctime)s | %(levelname)-8s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "colored",
                "stream": sys.stdout,
                "filters": ["sensitive_filter"],
            },
            "file_app": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": log_dir / "app.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["sensitive_filter"],
            },
            "file_error": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": log_dir / "errors.log",
                "maxBytes": 5 * 1024 * 1024,  # 5MB
                "backupCount": 3,
                "encoding": "utf-8",
                "filters": ["sensitive_filter"],
            },
            "file_access": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": log_dir / "access.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
                "filters": ["sensitive_filter"],
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
        "filters": {
            "sensitive_filter": {
                "()": SensitiveDataFilter,
            },
        },
    }

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Get main logger
    logger = logging.getLogger("app.main")

    # Print startup banner with dynamic info (safe characters only)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    startup_info = STARTUP_BANNER.format(timestamp=current_time, log_path=str(log_dir.absolute())[:45] + "...")
    print(startup_info)

    # Log startup messages (safe characters only)
    logger.info("=" * 65)
    logger.info("Artacom FTTH Billing API Server")
    logger.info(f"Log directory: {log_dir.absolute()}")
    logger.info("=" * 65)

    return logger


# --- Example Usage Functions ---


def log_system_health(logger: logging.Logger) -> None:
    """Log system health check"""
    if USE_UNICODE:
        logger.info("💊 System Health Check - All services running normally")
    else:
        logger.info("[HEALTH] System Health Check - All services running normally")


def log_startup_complete(logger: logging.Logger) -> None:
    """Log application startup completion"""
    if USE_UNICODE:
        logger.info("🚀 APPLICATION STARTUP COMPLETE - Ready to serve requests!")
    else:
        logger.info(">> APPLICATION STARTUP COMPLETE - Ready to serve requests!")


def log_shutdown(logger: logging.Logger) -> None:
    """Log application shutdown"""
    logger.info(">> Application shutting down gracefully...")
    logger.info(">> ARTACOM API SYSTEM - Goodbye!")


# --- Quick Test Function ---
if __name__ == "__main__":
    # Test the logging setup
    test_logger = setup_logging()

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
