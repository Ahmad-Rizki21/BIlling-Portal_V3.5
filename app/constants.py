"""
Application constants untuk menghilangkan magic numbers dan hard-coded values
"""

from typing import Any, Dict, List


# ================================
# Pagination & Limits
# ================================
class Pagination:
    DEFAULT_PAGE_SIZE = 15
    MAX_PAGE_SIZE = 100
    DEFAULT_EXPORT_LIMIT = 5000
    MAX_EXPORT_LIMIT = 50000
    MIN_SEARCH_LENGTH = 2


# ================================
# Status Constants
# ================================
class Status:
    # Pelanggan Status
    PELANGGAN_AKTIF = "Aktif"
    PELANGGAN_TIDAK_AKTIF = "Tidak Aktif"
    PELANGGAN_SUSPEND = "Suspend"
    PELANGGAN_PENDING = "Pending"

    # Invoice Status
    INVOICE_DRAFT = "Draft"
    INVOICE_MENUNGGU_PEMBAYARAN = "Menunggu Pembayaran"
    INVOICE_LUNAS = "Lunas"
    INVOICE_JATUH_TEMPO = "Jatuh Tempo"
    INVOICE_BATAL = "Batal"

    # Langganan Status
    LANGGANAN_AKTIF = "Aktif"
    LANGGANAN_TIDAK_AKTIF = "Tidak Aktif"
    LANGGANAN_SUSPEND = "Suspend"

    # Mikrotik Status
    MIKROTIK_CONNECTED = "Connected"
    MIKROTIK_DISCONNECTED = "Disconnected"
    MIKROTIK_ERROR = "Error"

    # User Status
    USER_AKTIF = True
    USER_TIDAK_AKTIF = False


# ================================
# HTTP Status Codes (Custom Messages)
# ================================
class HTTPMessages:
    NOT_FOUND_TEMPLATE = "{resource} tidak ditemukan"
    NOT_FOUND_WITH_ID_TEMPLATE = "{resource} dengan ID {id} tidak ditemukan"
    CONFLICT_TEMPLATE = "{field} '{value}' sudah ada"
    CREATE_SUCCESS_TEMPLATE = "Berhasil membuat {resource}"
    UPDATE_SUCCESS_TEMPLATE = "Berhasil mengupdate {resource}"
    DELETE_SUCCESS_TEMPLATE = "Berhasil menghapus {resource}"


# ================================
# Validation Rules
# ================================
class Validation:
    # Length limits
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    MAX_EMAIL_LENGTH = 255
    MAX_PHONE_LENGTH = 20
    MAX_NIK_LENGTH = 16
    MIN_NIK_LENGTH = 16

    # File sizes (in bytes)
    MAX_CSV_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

    # Allowed file extensions
    ALLOWED_CSV_EXTENSIONS = [".csv"]
    ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif"]

    # Network validation
    MIN_PORT = 1
    MAX_PORT = 65535
    IP_OCTET_MIN = 0
    IP_OCTET_MAX = 255


# ================================
# Business Rules
# ================================
class BusinessRules:
    # Payment due days
    PAYMENT_DUE_DAYS = 30
    REMINDER_DAYS_BEFORE_DUE = 7
    SUSPEND_DAYS_AFTER_DUE = 7

    # Mikrotik connection
    MIKROTIK_CONNECTION_TIMEOUT = 30  # seconds
    MIKROTIK_MAX_RETRY_ATTEMPTS = 3

    # Cache duration (in seconds)
    CACHE_DURATION_SHORT = 300  # 5 minutes
    CACHE_DURATION_MEDIUM = 1800  # 30 minutes
    CACHE_DURATION_LONG = 3600  # 1 hour

    # Job scheduling
    INVOICE_GENERATION_HOUR = 1  # 1 AM
    SUSPEND_SERVICE_HOUR = 2  # 2 AM
    PAYMENT_REMINDER_HOUR = 8  # 8 AM


# ================================
# Database Constraints
# ================================
class DatabaseConstraints:
    # Field lengths
    NAME_MAX_LENGTH = 255
    EMAIL_MAX_LENGTH = 255
    PHONE_MAX_LENGTH = 20
    ADDRESS_MAX_LENGTH = 500
    DESCRIPTION_MAX_LENGTH = 1000

    # ID constraints
    MIN_ID = 1


# ================================
# API Response Templates
# ================================
class APIResponse:
    SUCCESS_CODE = 200
    CREATED_CODE = 201
    NO_CONTENT_CODE = 204

    # Response structures
    SUCCESS_RESPONSE = {"status": "success", "message": ""}
    ERROR_RESPONSE = {"status": "error", "message": "", "detail": ""}


# ================================
# Notification Types
# ================================
class NotificationTypes:
    NEW_CUSTOMER = "new_customer_for_noc"
    NEW_DATA_TEKNIS = "new_data_teknis"
    NEW_INVOICE = "new_invoice"
    PAYMENT_RECEIVED = "payment_received"
    SERVICE_SUSPENDED = "service_suspended"
    MIKROTIK_ISSUE = "mikrotik_issue"
    SYSTEM_MESSAGE = "system"


# ================================
# Role Names
# ================================
class Roles:
    ADMIN = "Admin"
    NOC = "NOC"
    CS = "CS"
    FINANCE = "Finance"

    ROLE_COMBINATIONS = {
        "technical_teams": [NOC, CS, ADMIN],
        "finance_only": [FINANCE],
        "all_teams": [NOC, CS, ADMIN, FINANCE],
    }


# ================================
# File Upload Constants
# ================================
class FileUpload:
    # CSV Import templates
    PELANGGAN_CSV_HEADERS = [
        "Nama",
        "No KTP",
        "Email",
        "No Telepon",
        "Layanan",
        "Alamat",
        "Alamat 2",
        "Blok",
        "Unit",
        "Tanggal Instalasi (YYYY-MM-DD)",
        "ID Brand",
    ]

    DATA_TEKNIS_CSV_HEADERS = ["ID Pelanggan", "IP Pelanggan", "VLAN", "SN ONT", "Port ODP", "Port OLT", "Status"]

    # Sample data untuk templates
    PELANGGAN_SAMPLE_DATA = [
        {
            "Nama": "John Doe",
            "No KTP": "1234567890123456",
            "Email": "john@example.com",
            "No Telepon": "08123456789",
            "Layanan": "Internet 10Mbps",
            "Alamat": "Jl. Example No. 123",
            "Alamat 2": "RT 01/RW 02",
            "Blok": "A",
            "Unit": "123",
            "Tanggal Instalasi (YYYY-MM-DD)": "2024-01-15",
            "ID Brand": "JAKINET",
        }
    ]


# ================================
# Error Messages
# ================================
class ErrorMessages:
    # Authentication
    INVALID_CREDENTIALS = "Email atau password salah"
    INACTIVE_USER = "Akun tidak aktif"
    TOKEN_EXPIRED = "Token telah kadaluarsar"
    TOKEN_INVALID = "Token tidak valid"

    # Validation
    INVALID_EMAIL_FORMAT = "Format email tidak valid"
    INVALID_PHONE_FORMAT = "Format nomor telepon tidak valid"
    INVALID_NIK_FORMAT = "NIK harus 16 digit angka"
    INVALID_IP_FORMAT = "Format IP address tidak valid"

    # File upload
    INVALID_FILE_FORMAT = "Format file tidak valid"
    FILE_TOO_LARGE = "Ukuran file terlalu besar"
    EMPTY_FILE = "File kosong"

    # Database
    DATABASE_ERROR = "Terjadi kesalahan database"
    CONSTRAINT_VIOLATION = "Data melanggar constraint database"
    FOREIGN_KEY_VIOLATION = "Data terkait tidak ditemukan"

    # Business logic
    CUSTOMER_HAS_ACTIVE_SUBSCRIPTION = "Pelanggan memiliki langganan aktif"
    INVOICE_ALREADY_PAID = "Invoice sudah lunas"
    SERVICE_ALREADY_SUSPENDED = "Layanan sudah di-suspend"


# ================================
# Success Messages
# ================================
class SuccessMessages:
    USER_CREATED = "User berhasil dibuat"
    USER_UPDATED = "User berhasil diupdate"
    USER_DELETED = "User berhasil dihapus"

    PELANGGAN_CREATED = "Pelanggan berhasil dibuat"
    PELANGGAN_UPDATED = "Pelanggan berhasil diupdate"
    PELANGGAN_DELETED = "Pelanggan berhasil dihapus"

    INVOICE_CREATED = "Invoice berhasil dibuat"
    PAYMENT_RECORDED = "Pembayaran berhasil dicatat"

    FILE_IMPORTED = "File berhasil diimport"
    DATA_EXPORTED = "Data berhasil diekspor"


# ================================
# Log Messages
# ================================
class LogMessages:
    # Operations
    OPERATION_START = "Memulai {operation} {resource}"
    OPERATION_SUCCESS = "Berhasil {operation} {resource} dengan ID {id}"
    OPERATION_FAILED = "Gagal {operation} {resource}: {error}"

    # Authentication
    LOGIN_SUCCESS = "User {email} berhasil login"
    LOGIN_FAILED = "Login gagal untuk email {email}"
    LOGOUT_SUCCESS = "User {email} berhasil logout"

    # System
    SCHEDULER_STARTED = "Scheduler berhasil dimulai"
    DATABASE_CONNECTED = "Database berhasil terkoneksi"
    WEBSOCKET_CONNECTED = "WebSocket terkoneksi untuk user {user_id}"


# ================================
# Configuration Defaults
# ================================
class ConfigDefaults:
    # Development
    DEBUG_MODE = True
    LOG_LEVEL = "INFO"

    # Production
    PRODUCTION_DEBUG_MODE = False
    PRODUCTION_LOG_LEVEL = "WARNING"

    # CORS
    DEFAULT_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"]

    # Middleware
    CORS_MAX_AGE = 600  # 10 minutes
    GZIP_MIN_SIZE = 1000  # bytes

    # Session
    SESSION_TIMEOUT = 1800  # 30 minutes


# ================================
# Regex Patterns
# ================================
class RegexPatterns:
    EMAIL = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    PHONE_INDONESIA = r"^(\+62|62|0)[0-9]{9,13}$"
    IP_ADDRESS = r"^(\d{1,3}\.){3}\d{1,3}$"
    NIK = r"^\d{16}$"
    PASSWORD_STRENGTH = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"


# ================================
# Time Formats
# ================================
class TimeFormats:
    DATE_ONLY = "%Y-%m-%d"
    DATETIME = "%Y-%m-%d %H:%M:%S"
    ISO_DATETIME = "%Y-%m-%dT%H:%M:%S"
    TIMESTAMP = "%Y%m%d_%H%M%S"


# ================================
# Export/Import Constants
# ================================
class ExportImport:
    # CSV Encoding
    DEFAULT_ENCODING = "utf-8"
    EXCEL_COMPATIBLE_ENCODING = "utf-8-sig"

    # Delimiters
    CSV_DELIMITER = ","
    EXCEL_CSV_DELIMITER = ";"

    # File naming
    EXPORT_FILENAME_PATTERN = "{prefix}_{timestamp}.csv"
    TEMPLATE_FILENAME_PATTERN = "template_{prefix}_{timestamp}.csv"


# ================================
# API Rate Limiting
# ================================
class RateLimiting:
    LOGIN_ATTEMPTS = 5
    LOGIN_WINDOW = 300  # 5 minutes
    API_REQUESTS_PER_MINUTE = 100
    API_REQUESTS_PER_HOUR = 1000


# ================================
# WebSocket Constants
# ================================
class WebSocket:
    CONNECTION_TIMEOUT = 300  # 5 minutes
    HEARTBEAT_INTERVAL = 30  # 30 seconds
    MAX_CONNECTIONS_PER_USER = 5


# ================================
# Feature Flags
# ================================
class Features:
    ENABLE_EMAIL_NOTIFICATIONS = True
    ENABLE_SMS_NOTIFICATIONS = False
    ENABLE_DASHBOARD_CACHE = True
    ENABLE_ADVANCED_SEARCH = True
    ENABLE_BULK_OPERATIONS = True
    ENABLE_EXPORT_SCHEDULING = False
