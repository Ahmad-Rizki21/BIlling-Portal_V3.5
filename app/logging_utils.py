"""
Utility functions for secure logging that filter out sensitive data
"""

import json
import logging
import re
from typing import Any, Dict, Union, cast


class SensitiveDataFilter(logging.Filter):
    """
    A logging filter that removes sensitive data from log records
    """

    # Patterns to identify sensitive fields
    SENSITIVE_PATTERNS = {
        "password": re.compile(r".*(password|passwd|pwd).*", re.IGNORECASE),
        "token": re.compile(r".*(token|jwt|auth|authorization).*", re.IGNORECASE),
        "personal": re.compile(
            r".*(ktp|nik|no_ktp|no_ktp|nomor_ktp|ktp_number|identity|identitas).*",
            re.IGNORECASE,
        ),
        "financial": re.compile(r".*(credit|debit|card|kartu|rekening|account|acc).*", re.IGNORECASE),
        "credentials": re.compile(r".*(credential|creds|login|username|user).*", re.IGNORECASE),
        "address": re.compile(r".*(alamat|address|location|lokasi).*", re.IGNORECASE),
        "phone": re.compile(r".*(phone|telepon|telp|no_telp|phone_number|mobile).*", re.IGNORECASE),
        "email": re.compile(r".*(email|mail).*", re.IGNORECASE),
    }

    # Specific field names that contain sensitive data
    SENSITIVE_FIELDS = {
        "password",
        "passwd",
        "pwd",
        "secret",
        "token",
        "jwt",
        "auth_token",
        "authorization",
        "auth",
        "api_key",
        "api_secret",
        "private_key",
        "no_ktp",
        "ktp",
        "nik",
        "identity_number",
        "identity",
        "credit_card",
        "debit_card",
        "card_number",
        "kartu_kredit",
        "rekening",
        "account_number",
        "bank_account",
        "alamat",
        "address",
        "location",
        "lokasi",
        "no_telp",
        "phone",
        "telepon",
        "mobile",
        "phone_number",
        "email",
        "mail",
        "mikrotik_password",
        "router_password",
        "device_password",
        "pppoe_password",
        "password_pppoe",
        "xendit_key",
        "payment_key",
        "api_key",
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter the log record to remove sensitive data
        """
        # Filter the message
        if hasattr(record, "msg"):
            record.msg = self._filter_sensitive_data(record.msg)

        # Filter args if they exist
        if hasattr(record, "args") and record.args:
            if isinstance(record.args, dict):
                # Handle named arguments
                filtered_args: Dict[str, Any] = {}
                for key, value in record.args.items():
                    if self._is_sensitive_field(key):
                        filtered_args[key] = "***REDACTED***"
                    else:
                        filtered_args[key] = self._filter_sensitive_data(value)
                record.args = filtered_args  # type: ignore
            elif isinstance(record.args, (list, tuple)):
                # Handle positional arguments
                filtered_args = []
                for value in record.args:
                    filtered_args.append(self._filter_sensitive_data(value))
                record.args = tuple(filtered_args)  # type: ignore

        return True

    def _is_sensitive_field(self, field_name: str) -> bool:
        """
        Check if a field name contains sensitive data
        """
        field_lower = field_name.lower()

        # Direct match
        if field_lower in self.SENSITIVE_FIELDS:
            return True

        # Pattern matching
        for pattern_name, pattern in self.SENSITIVE_PATTERNS.items():
            if pattern.match(field_lower):
                return True

        return False

    def _filter_sensitive_data(self, data: Any) -> Any:
        """
        Recursively filter sensitive data from various data types
        """
        if isinstance(data, str):
            # Check if it's a JSON string
            if self._is_json_string(data):
                try:
                    json_data = json.loads(data)
                    filtered_json = self._filter_sensitive_data(json_data)
                    return json.dumps(filtered_json, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError):
                    # If it fails, treat as regular string
                    pass

            # Check if it contains sensitive patterns
            if self._contains_sensitive_patterns(data):
                return "***REDACTED***"

            return data

        elif isinstance(data, dict):
            filtered_dict = {}
            for key, value in data.items():
                if self._is_sensitive_field(key):
                    filtered_dict[key] = "***REDACTED***"
                else:
                    filtered_dict[key] = self._filter_sensitive_data(value)
            return filtered_dict

        elif isinstance(data, (list, tuple)):
            filtered_list = []
            for item in data:
                filtered_list.append(self._filter_sensitive_data(item))
            return type(data)(filtered_list)

        elif isinstance(data, (int, float, bool, type(None))):
            return data

        else:
            # For other types, convert to string and check
            str_data = str(data)
            if self._contains_sensitive_patterns(str_data):
                return "***REDACTED***"
            return data

    def _is_json_string(self, data: str) -> bool:
        """
        Check if a string is a valid JSON
        """
        data = data.strip()
        return (data.startswith("{") and data.endswith("}")) or (data.startswith("[") and data.endswith("]"))

    def _contains_sensitive_patterns(self, data: str) -> bool:
        """
        Check if a string contains sensitive data patterns
        """
        data_lower = data.lower()

        # Check for common sensitive data patterns
        sensitive_patterns = [
            r"[0-9]{16}",  # 16-digit numbers (credit cards, KTP)
            r"password[\\s]*[=:]",
            r"token[\\s]*[=:]",
            r"auth[\\s]*[=:]",
            r"authorization[\\s]*[=:]",
            r"Bearer\\s+[A-Za-z0-9\\-_]+\\.[A-Za-z0-9\\-_]+\\.[A-Za-z0-9\\-_]+",  # JWT tokens
            r"Basic\\s+[A-Za-z0-9+/=]+",  # Basic auth
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                return True

        return False


def sanitize_log_data(data: Union[Dict, str, Any]) -> Union[Dict, str, Any]:
    """
    Sanitize data before logging by removing sensitive information

    Args:
        data: Data to sanitize (dict, string, or other types)

    Returns:
        Sanitized data with sensitive information removed
    """
    filter_instance = SensitiveDataFilter()
    return filter_instance._filter_sensitive_data(data)


def log_request_safe(logger: logging.Logger, level: int, message: str, request_data: Dict | None = None):
    """
    Log request data safely by filtering sensitive information

    Args:
        logger: Logger instance
        level: Logging level
        message: Log message
        request_data: Request data to log (will be sanitized)
    """
    if request_data:
        sanitized_data = sanitize_log_data(request_data)
        logger.log(level, f"{message} | Request data: {sanitized_data}")
    else:
        logger.log(level, message)


def setup_secure_logging() -> None:
    """
    Setup logging with sensitive data filtering
    """
    # Get the root logger
    root_logger = logging.getLogger()

    # Add the sensitive data filter to all handlers
    sensitive_filter = SensitiveDataFilter()

    for handler in root_logger.handlers:
        handler.addFilter(sensitive_filter)

    # Also add to specific loggers used in the application
    app_logger = logging.getLogger("app")
    for handler in app_logger.handlers:
        if sensitive_filter not in handler.filters:
            handler.addFilter(sensitive_filter)

    api_logger = logging.getLogger("app.api")
    for handler in api_logger.handlers:
        if sensitive_filter not in handler.filters:
            handler.addFilter(sensitive_filter)

    middleware_logger = logging.getLogger("app.middleware")
    for handler in middleware_logger.handlers:
        if sensitive_filter not in handler.filters:
            handler.addFilter(sensitive_filter)


# Example usage:
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Setup secure logging
    setup_secure_logging()

    # Get logger
    logger = logging.getLogger(__name__)

    # Test logging with sensitive data
    logger.info(
        "User login attempt",
        extra={
            "username": "testuser",
            "password": "secret123",
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        },
    )

    # Test with JSON data
    sensitive_json = {
        "user": "john_doe",
        "password": "mysecretpassword",
        "ktp": "1234567890123456",
        "address": "Jalan Merdeka No. 123",
        "phone": "081234567890",
    }

    logger.info(f"User data: {json.dumps(sensitive_json)}")
