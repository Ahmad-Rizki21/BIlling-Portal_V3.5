"""
Environment validation utilities untuk memastikan semua required variables terconfigure.
"""

import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Required environment variables untuk production
REQUIRED_ENV_VARS = [
    "DATABASE_URL",
    "SECRET_KEY",
    "ENCRYPTION_KEY",
    "XENDIT_SECRET_KEY",
    "MAPBOX_ACCESS_TOKEN",
]

# Optional environment variables dengan default values
OPTIONAL_ENV_VARS = {
    "ENVIRONMENT": "development",
    "FRONTEND_URL": "",
    "LOG_LEVEL": "INFO",
    "CORS_ORIGINS": "",
}


class EnvironmentValidationError(Exception):
    """Exception untuk environment validation errors."""

    pass


def validate_environment() -> Dict[str, Any]:
    """
    Validate semua environment variables yang dibutuhkan.

    Returns:
        Dictionary dengan environment configuration

    Raises:
        EnvironmentValidationError: Jika required variables missing
    """
    errors = []
    config = {}

    logger.info("🔍 Starting environment validation...")

    # Check required variables
    for var_name in REQUIRED_ENV_VARS:
        value = os.getenv(var_name)
        if not value or value.strip() == "":
            errors.append(f"Missing required environment variable: {var_name}")
        else:
            config[var_name] = value
            # Mask sensitive values in logs
            if "SECRET" in var_name or "KEY" in var_name:
                logger.info(f"✅ {var_name}: {'*' * (len(value) // 4)}****")
            else:
                logger.info(f"✅ {var_name}: {value[:50]}{'...' if len(value) > 50 else ''}")

    # Check optional variables dengan defaults
    for var_name, default_value in OPTIONAL_ENV_VARS.items():
        value = os.getenv(var_name, default_value)
        config[var_name] = value
        logger.info(f"✅ {var_name}: {value} (default: {default_value})")

    # Security-specific validations
    if "SECRET_KEY" in config:
        secret_key = config["SECRET_KEY"]
        if len(secret_key) < 32:
            errors.append(f"SECRET_KEY too short (minimum 32 characters, got {len(secret_key)})")

    if "ENCRYPTION_KEY" in config:
        encryption_key = config["ENCRYPTION_KEY"]
        if len(encryption_key) < 32:
            errors.append(f"ENCRYPTION_KEY too short (minimum 32 characters, got {len(encryption_key)})")

    # Database-specific validations
    if "DATABASE_URL" in config:
        db_url = config["DATABASE_URL"]
        if not db_url.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite:///")):
            errors.append(f"Invalid DATABASE_URL format: {db_url[:20]}...")

    # Environment-specific validations
    environment = config.get("ENVIRONMENT", "development")
    if environment == "production":
        # Production-specific checks
        if config.get("SECRET_KEY") == "your-secret-key-here":
            errors.append("Default SECRET_KEY detected in production environment")
        if config.get("ENCRYPTION_KEY") == "your-encryption-key-here":
            errors.append("Default ENCRYPTION_KEY detected in production environment")

        # Check for CORS configuration
        if not config.get("FRONTEND_URL"):
            errors.append("FRONTEND_URL must be configured in production environment")

    if errors:
        error_message = "Environment validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        logger.error(f"❌ {error_message}")
        raise EnvironmentValidationError(error_message)

    logger.info("🎉 Environment validation completed successfully!")
    return config


def get_security_headers() -> Dict[str, str]:
    """
    Get security headers berdasarkan environment configuration.

    Returns:
        Dictionary dengan security headers
    """
    environment = os.getenv("ENVIRONMENT", "development")

    security_headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }

    # Production-specific headers
    if environment == "production":
        security_headers.update(
            {
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';",
            }
        )

    return security_headers


def log_security_status():
    """Log security status configuration."""
    try:
        config = validate_environment()

        environment = config.get("ENVIRONMENT", "development")
        logger.info(f"🔒 Security Status for {environment.upper()} environment:")

        # Log security features
        security_features = [
            ("Environment", environment),
            ("Database", "Configured" if "DATABASE_URL" in config else "Missing"),
            ("Secret Key", "Configured" if "SECRET_KEY" in config else "Missing"),
            ("Encryption Key", "Configured" if "ENCRYPTION_KEY" in config else "Missing"),
            ("Xendit Integration", "Configured" if "XENDIT_SECRET_KEY" in config else "Missing"),
            ("Mapbox Integration", "Configured" if "MAPBOX_ACCESS_TOKEN" in config else "Missing"),
        ]

        for feature, status in security_features:
            logger.info(f"  • {feature}: {status}")

        # Security warnings
        warnings = []
        if environment == "production":
            if not config.get("FRONTEND_URL"):
                warnings.append("Frontend URL not configured")
            if "localhost" in config.get("DATABASE_URL", ""):
                warnings.append("Using localhost database in production")

        if warnings:
            logger.warning("⚠️  Security Warnings:")
            for warning in warnings:
                logger.warning(f"  • {warning}")

    except EnvironmentValidationError as e:
        logger.error(f"🚨 Environment Validation Failed: {e}")
        raise


# Validate environment saat module di-import
try:
    ENV_CONFIG = validate_environment()
    SECURITY_HEADERS = get_security_headers()
    log_security_status()
except EnvironmentValidationError:
    # Jika environment validation gagal, log tapi tidak crash app
    logger.error("Environment validation failed - application may not work correctly")
    ENV_CONFIG = {}
    SECURITY_HEADERS = get_security_headers()
