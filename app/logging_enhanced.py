# Enhanced System Logging Module
# =================================
# Provides professional logging with structured output and beautiful formatting

import logging
import logging.config
import os
import platform
import sys
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

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

SHUTDOWN_BANNER = """
+-------------------------------------------------------------+
|  >> SYSTEM STATUS: SHUTTING DOWN...                        |
|  >> Shutdown Time: {timestamp}                               |
|  >> Session Duration: {duration}                            |
|  >> Graceful shutdown completed                              |
+-------------------------------------------------------------+
"""


# --- Logging Levels with Icons ---
class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# --- Detect Terminal Capabilities ---
def can_use_unicode() -> bool:
    """Check if terminal supports Unicode characters"""
    try:
        # Check if we're in Windows cmd
        if platform.system() == "Windows":
            # Check for modern terminals
            if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM"):
                return True
            return False
        return True
    except:
        return False


USE_UNICODE = can_use_unicode()

# --- Icon Sets for Different Log Types ---
ICONS = {
    "unicode": {
        "startup": "🚀",
        "shutdown": "🛑",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "debug": "🔍",
        "database": "🗄️",
        "api": "🌐",
        "scheduler": "⏰",
        "payment": "💳",
        "mikrotik": "📡",
        "websocket": "🔌",
        "auth": "🔐",
        "maintenance": "🔧",
        "health": "💊",
        "performance": "⚡",
        "security": "🛡️",
    },
    "ascii": {
        "startup": "[START]",
        "shutdown": "[STOP]",
        "success": "[OK]",
        "error": "[FAIL]",
        "warning": "[WARN]",
        "info": "[INFO]",
        "debug": "[DEBUG]",
        "database": "[DB]",
        "api": "[API]",
        "scheduler": "[SCHED]",
        "payment": "[PAY]",
        "mikrotik": "[MIKRO]",
        "websocket": "[WS]",
        "auth": "[AUTH]",
        "maintenance": "[MAINT]",
        "health": "[HEALTH]",
        "performance": "[PERF]",
        "security": "[SEC]",
    },
}

# Get appropriate icon set
ICONS_SET = ICONS["unicode"] if USE_UNICODE else ICONS["ascii"]


# --- Color Definitions ---
class Colors:
    """ANSI color codes for terminal output"""

    if USE_UNICODE:
        # Full color support
        RESET = "\033[0m"
        BLACK = "\033[30m"
        RED = "\033[31m"
        GREEN = "\033[32m"
        YELLOW = "\033[33m"
        BLUE = "\033[34m"
        MAGENTA = "\033[35m"
        CYAN = "\033[36m"
        WHITE = "\033[37m"
        BRIGHT_BLACK = "\033[90m"
        BRIGHT_RED = "\033[91m"
        BRIGHT_GREEN = "\033[92m"
        BRIGHT_YELLOW = "\033[93m"
        BRIGHT_BLUE = "\033[94m"
        BRIGHT_MAGENTA = "\033[95m"
        BRIGHT_CYAN = "\033[96m"
        BRIGHT_WHITE = "\033[97m"
    else:
        # Limited color support for Windows cmd
        RESET = ""
        BLACK = ""
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        BRIGHT_BLACK = ""
        BRIGHT_RED = ""
        BRIGHT_GREEN = ""
        BRIGHT_YELLOW = ""
        BRIGHT_BLUE = ""
        BRIGHT_MAGENTA = ""
        BRIGHT_CYAN = ""
        BRIGHT_WHITE = ""


# --- Enhanced Formatters ---
class EnhancedColoredFormatter(logging.Formatter):
    """Enhanced formatter with beautiful colors and structure"""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BRIGHT_MAGENTA,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.use_colors = USE_UNICODE

    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        level_color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        level_name = f"{level_color}{record.levelname:<8}{Colors.RESET}"

        # Clean module name
        module_name = record.name.replace("app.", "").upper()
        if len(module_name) > 12:
            module_name = module_name[:9] + "..."
        module_name = f"{Colors.BRIGHT_BLUE}{module_name:<12}{Colors.RESET}"

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        timestamp = f"{Colors.BRIGHT_BLACK}{timestamp}{Colors.RESET}"

        # Add separator
        separator = "|" if USE_UNICODE else "|"
        separator = f"{Colors.BRIGHT_BLACK}{separator}{Colors.RESET}"

        # Format the message
        formatted = super().format(record)

        return f"{timestamp} {separator} {module_name} {separator} {level_name} {separator} {formatted}"


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)  # type: ignore

        import json

        return json.dumps(log_entry, ensure_ascii=False)


class FileFormatter(logging.Formatter):
    """Clean formatter for file output without colors"""

    def format(self, record: logging.LogRecord) -> str:
        record.name = record.name.replace("app.", "").upper()
        return super().format(record)


# --- Specialized Logger Classes ---
class StructuredLogger:
    """Enhanced logger with structured output"""

    def __init__(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.name = name

    def _log_with_structure(
        self, level: int, message: str, icon: str = "", extra: Optional[Dict[str, Any]] = None, color: str = ""
    ) -> None:
        """Internal method for structured logging"""
        if extra:
            extra_data = extra.copy()
            # Add icon to extra data
            if icon:
                extra_data["icon"] = icon
            if color:
                extra_data["color"] = color
            self.logger.log(level, message, extra={"extra_data": extra_data})
        else:
            if icon and color:
                colored_message = f"{color}{icon} {message}{Colors.RESET}"
                self.logger.log(level, colored_message)
            else:
                self.logger.log(level, message)

    def debug(self, message: str, **kwargs) -> None:
        icon = ICONS_SET.get("debug", "")
        self._log_with_structure(logging.DEBUG, message, icon, extra=kwargs, color=Colors.CYAN)

    def info(self, message: str, **kwargs) -> None:
        icon = ICONS_SET.get("info", "")
        self._log_with_structure(logging.INFO, message, icon, extra=kwargs, color=Colors.GREEN)

    def warning(self, message: str, **kwargs) -> None:
        icon = ICONS_SET.get("warning", "")
        self._log_with_structure(logging.WARNING, message, icon, extra=kwargs, color=Colors.YELLOW)

    def error(self, message: str, exc_info: bool = False, **kwargs) -> None:
        icon = ICONS_SET.get("error", "")
        if exc_info:
            self.logger.error(message, exc_info=True)
        else:
            self._log_with_structure(logging.ERROR, message, icon, extra=kwargs, color=Colors.RED)

    def critical(self, message: str, **kwargs) -> None:
        icon = ICONS_SET.get("error", "")
        self._log_with_structure(logging.CRITICAL, message, icon, extra=kwargs, color=Colors.BRIGHT_RED)


# --- Helper Functions for Specific Log Types ---
def log_system_event(logger: logging.Logger, event_type: str, message: str, status: str = "info", details: str = "") -> None:
    """Log system events with appropriate icons"""
    icons = {
        "startup": ICONS_SET.get("startup", ""),
        "shutdown": ICONS_SET.get("shutdown", ""),
        "health": ICONS_SET.get("health", ""),
        "maintenance": ICONS_SET.get("maintenance", ""),
        "performance": ICONS_SET.get("performance", ""),
        "security": ICONS_SET.get("security", ""),
    }

    status_colors = {
        "success": Colors.GREEN,
        "error": Colors.RED,
        "warning": Colors.YELLOW,
        "info": Colors.BLUE,
    }

    icon = icons.get(event_type, ICONS_SET.get("info", ""))
    color = status_colors.get(status, Colors.BLUE)

    colored_message = f"{color}{icon} {message}{Colors.RESET}"

    if details:
        colored_message += f" | {details}"

    if status == "error":
        logger.error(colored_message)
    elif status == "warning":
        logger.warning(colored_message)
    else:
        logger.info(colored_message)


def log_scheduler_event(logger: logging.Logger, job_name: str, status: str, details: str = "") -> None:
    """Enhanced scheduler logging"""
    status_icons = {
        "started": ICONS_SET.get("scheduler", ""),
        "completed": ICONS_SET.get("success", ""),
        "failed": ICONS_SET.get("error", ""),
        "skipped": ICONS_SET.get("warning", ""),
    }

    icon = status_icons.get(status, ICONS_SET.get("info", ""))
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
    status_icons = {
        "success": ICONS_SET.get("success", ""),
        "failed": ICONS_SET.get("error", ""),
        "info": ICONS_SET.get("info", ""),
        "connecting": ICONS_SET.get("websocket", ""),
        "timeout": ICONS_SET.get("warning", ""),
    }

    icon = status_icons.get(status, ICONS_SET.get("info", ""))
    message = f"{icon} MikroTik | {operation} for Customer: '{customer_id}'"

    if details:
        message += f" | {details}"

    if status in ["failed", "timeout"]:
        logger.error(message)
    elif status == "success":
        logger.info(message)
    else:
        logger.info(message)


def log_payment_event(logger: logging.Logger, event: str, invoice_id: str, amount: str = "", details: str = "") -> None:
    """Enhanced payment event logging"""
    event_icons = {
        "created": ICONS_SET.get("info", ""),
        "paid": ICONS_SET.get("success", ""),
        "failed": ICONS_SET.get("error", ""),
        "pending": ICONS_SET.get("warning", ""),
        "cancelled": ICONS_SET.get("error", ""),
        "refunded": ICONS_SET.get("info", ""),
    }

    icon = event_icons.get(event.lower(), ICONS_SET.get("payment", ""))
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
    status_icons = {
        "success": ICONS_SET.get("success", ""),
        "failed": ICONS_SET.get("error", ""),
        "connecting": ICONS_SET.get("info", ""),
        "migrating": ICONS_SET.get("warning", ""),
    }

    icon = status_icons.get(status, ICONS_SET.get("database", ""))
    message = f"{icon} Database | {operation} on '{table}'"

    if details:
        message += f" | {details}"

    if status == "failed":
        logger.error(message)
    else:
        logger.info(message)


def log_api_request(
    logger: logging.Logger, method: str, endpoint: str, status_code: int, duration: float | None = None, user_info: str = "Anonymous"
) -> None:
    """API request logging with performance metrics"""
    if USE_UNICODE:
        status_icon = "✅" if 200 <= status_code < 300 else "⚠️" if 300 <= status_code < 400 else "❌"
    else:
        status_icon = "[OK]" if 200 <= status_code < 300 else "[WARN]" if 300 <= status_code < 400 else "[ERR]"

    message = f"{status_icon} [{method}] {endpoint} -> {status_code}"

    if duration:
        message += f" | {duration:.2f}ms"

    if user_info != "Anonymous":
        message += f" | User: {user_info}"

    if status_code >= 400:
        logger.warning(message)
    else:
        logger.info(message)


def log_websocket_event(logger: logging.Logger, event: str, user_id: str, details: str = "") -> None:
    """WebSocket event logging"""
    event_icons = {
        "connect": ICONS_SET.get("websocket", ""),
        "disconnect": ICONS_SET.get("warning", ""),
        "message": ICONS_SET.get("info", ""),
        "error": ICONS_SET.get("error", ""),
    }

    icon = event_icons.get(event, ICONS_SET.get("info", ""))
    message = f"{icon} WebSocket | {event} for User: '{user_id}'"

    if details:
        message += f" | {details}"

    if event == "error":
        logger.error(message)
    else:
        logger.info(message)


def log_auth_event(logger: logging.Logger, event: str, user_id: str = "", details: str = "") -> None:
    """Authentication event logging"""
    event_icons = {
        "login": ICONS_SET.get("success", ""),
        "logout": ICONS_SET.get("warning", ""),
        "failed": ICONS_SET.get("error", ""),
        "token_expired": ICONS_SET.get("warning", ""),
        "unauthorized": ICONS_SET.get("error", ""),
    }

    icon = event_icons.get(event, ICONS_SET.get("auth", ""))
    message = f"{icon} Auth | {event}"

    if user_id:
        message += f" | User: '{user_id}'"

    if details:
        message += f" | {details}"

    if event in ["failed", "unauthorized"]:
        logger.warning(message)
    else:
        logger.info(message)


# --- Core Logging Setup ---
def setup_logging() -> logging.Logger:
    """Enhanced logging setup with beautiful formatting"""

    # Create log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Print ASCII Art Banner
    print(ARTACOM_ASCII)

    # Configuration dictionary
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": EnhancedColoredFormatter,
                "format": "%(message)s",
                "datefmt": "%H:%M:%S",
            },
            "json": {
                "()": JSONFormatter,
                "format": "%(message)s",
            },
            "detailed": {
                "()": FileFormatter,
                "format": "%(asctime)s | %(name)-15s | %(levelname)-8s | %(funcName)-20s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {
                "()": FileFormatter,
                "format": "%(asctime)s | %(levelname)-8s | %(message)s",
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
            "file_json": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": log_dir / "structured.log",
                "maxBytes": 10 * 1024 * 1024,  # 10MB
                "backupCount": 5,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "app": {
                "handlers": ["console", "file_app", "file_error", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "app.api": {
                "handlers": ["console", "file_access", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "app.auth": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "app.database": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "app.mikrotik": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "app.scheduler": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "handlers": ["file_app", "file_json"],
                "level": "WARNING",
                "propagate": False,
            },
            "sqlalchemy.pool": {
                "handlers": ["file_app", "file_json"],
                "level": "WARNING",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["file_access", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
            "apscheduler": {
                "handlers": ["console", "file_app", "file_json"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file_app", "file_error"],
        },
    }

    # Apply logging configuration
    logging.config.dictConfig(logging_config)

    # Get main logger
    main_logger = logging.getLogger("app.main")

    # Print startup banner
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    startup_info = STARTUP_BANNER.format(timestamp=current_time, log_path=str(log_dir.absolute())[:45] + "...")
    print(startup_info)

    # Log startup messages
    separator = "|" if USE_UNICODE else "|"
    main_logger.info("=" * 60)
    log_system_event(main_logger, "startup", "Enhanced logging system initialized!", "success")
    log_system_event(main_logger, "health", "All logging handlers active", "success")
    main_logger.info(f"Log files stored in: {log_dir.absolute()}")
    main_logger.info(f"Startup time: {current_time}")
    main_logger.info(f"Unicode support: {USE_UNICODE}")
    main_logger.info("=" * 60)

    return main_logger


# --- Utility Functions ---
def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance"""
    return StructuredLogger(name)


def log_exception(logger: logging.Logger, exception: Exception, context: str = "") -> None:
    """Log exception with full traceback"""
    error_msg = f"Exception in {context}: {str(exception)}"
    tb = traceback.format_exc()

    logger.error(f"{error_msg}\n{tb}")


# --- Shutdown Handler ---
def setup_shutdown_handler(start_time: datetime) -> callable:
    """Setup graceful shutdown logging"""

    def shutdown_handler() -> None:
        # Calculate uptime
        uptime = datetime.now() - start_time
        uptime_str = str(uptime).split(".")[0]  # Remove microseconds

        # Print shutdown banner
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shutdown_info = SHUTDOWN_BANNER.format(timestamp=current_time, duration=uptime_str)
        print(shutdown_info)

        # Log shutdown
        logger = logging.getLogger("app.main")
        log_system_event(logger, "shutdown", "Application shutdown complete", "success")

    return shutdown_handler


# --- Quick Test Function ---
if __name__ == "__main__":
    # Test the enhanced logging setup
    test_logger = setup_logging()

    # Test different log types
    log_system_event(test_logger, "startup", "System initialization", "success")
    log_scheduler_event(test_logger, "daily_billing", "started", "Processing 150 customers")
    log_mikrotik_operation(test_logger, "disconnect_user", "CUST001", "success", "User disconnected")
    log_payment_event(test_logger, "paid", "INV-2024-001", "Rp 150,000", "Bank transfer")
    log_database_event(test_logger, "backup", "customers", "success", "1,250 records")
    log_api_request(test_logger, "POST", "/api/v1/customers", 201, 145.5, "admin")
    log_websocket_event(test_logger, "connect", "user123", "WebSocket connected")
    log_auth_event(test_logger, "login", "user123", "Successful login")

    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
