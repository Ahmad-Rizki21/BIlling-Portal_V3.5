# Simple Logging Configuration
# ==========================
# Basic logging setup that doesn't change existing behavior

import logging
import logging.config
import sys
from datetime import datetime
from pathlib import Path


def setup_simple_logging():
    """Setup simple logging without changing existing behavior"""

    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Create handlers
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    error_handler = logging.FileHandler(log_dir / "errors.log", encoding="utf-8")
    error_handler.setLevel(logging.ERROR)

    # Set formatter
    formatter = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Get main logger
    logger = logging.getLogger("app.main")

    # Simple startup message
    print("=" * 60)
    logger.info("Artacom FTTH Billing API Server")
    logger.info(f"Log directory: {log_dir.absolute()}")
    logger.info("=" * 60)

    return logger


def get_logger(name):
    """Get a logger instance"""
    return logging.getLogger(name)


# Quick test function
if __name__ == "__main__":
    logger = setup_simple_logging()
    logger.info("Logging system initialized")
    logger.warning("This is a warning")
    logger.error("This is an error")
