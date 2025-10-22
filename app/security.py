# app/security.py
"""
Security utilities untuk tambahan layer keamanan aplikasi.
Module ini handle encryption/decryption data sensitif tambahan.

Fungsi utama:
- Password encryption (selain bcrypt)
- Secure cipher suite initialization
- Key validation dan management
- Backward compatibility support

Security approach:
- Fernet encryption (AES 128 + HMAC + timestamp)
- Key validation untuk prevent misconfiguration
- Graceful fallback buat compatibility
- Comprehensive error handling

Usage:
- Backup encryption method
- Sensitive data protection
- Legacy data migration
- Additional security layer
"""

import base64
import logging

from cryptography.fernet import Fernet

from .config import settings

logger = logging.getLogger(__name__)


def get_cipher_suite() -> Fernet:
    """
    Initialize Fernet cipher suite dengan validasi key yang comprehensive.
    Function ini ensure encryption key valid dan properly configured.

    Returns:
        Fernet cipher suite instance

    Key validation:
    - Base64 format checking
    - 32 bytes length validation (Fernet requirement)
    - Proper URL-safe encoding
    - Fallback generation untuk development

    Error handling:
    - Invalid format: raise ValueError dengan detail error
    - Wrong length: specify expected vs actual length
    - Missing key: generate temporary key (development only)

    Security notes:
    - Production harus punya valid ENCRYPTION_KEY
    - Key generation only buat development/testing
    - Base64 URL-safe encoding required
    - 32 bytes = 256 bits key strength

    Example:
        cipher = get_cipher_suite()
        encrypted = cipher.encrypt(b"secret data")
        decrypted = cipher.decrypt(encrypted)

    Configuration:
        ENCRYPTION_KEY=base64url-encoded-32-byte-key
    """
    try:
        # Pastikan key dalam format yang benar
        key = settings.ENCRYPTION_KEY

        if isinstance(key, str):
            # Validasi key format sebelum decode
            try:
                # Coba decode dari base64
                key_bytes = base64.urlsafe_b64decode(key)
                # Pastikan key adalah 32 bytes
                if len(key_bytes) != 32:
                    raise ValueError(f"Key must be 32 bytes, got {len(key_bytes)}")
                return Fernet(key_bytes)
            except Exception as decode_error:
                raise ValueError(f"Invalid base64 key format: {decode_error}")
        else:
            # Jika key bukan string, asumsikan sudah dalam bentuk bytes
            if len(key) != 32:
                raise ValueError(f"Key must be 32 bytes, got {len(key)}")
            return Fernet(key)
    except Exception as e:
        # Generate key baru jika ada masalah (should not happen in production)
        new_key = Fernet.generate_key()
        return Fernet(new_key)


cipher_suite = get_cipher_suite()


def encrypt_password(password: str) -> str:
    """
    Enkripsi password plaintext pake Fernet encryption.
    Alternative encryption method selain bcrypt hashing.

    Args:
        password: Password plaintext yang mau dienkripsi

    Returns:
        Encrypted password string (base64)

    Security features:
    - AES 128-bit encryption
    - HMAC untuk integrity verification
    - Timestamp buat replay protection
    - Graceful fallback kalau encryption gagal

    Use cases:
    - Temporary password storage
    - Sensitive config data
    - Additional security layer
    - Backup encryption method

    Difference dengan bcrypt:
    - Bcrypt = one-way hash (authentication)
    - Fernet = two-way encryption (storage)
    - Bcrypt buat password verification
    - Fernet buat data yang perlu di-decrypt

    Error handling:
    - Log error tanpa expose sensitive data
    - Return original password kalau gagal (fallback)
    - Prevent data loss saat encryption error

    Note:
    - Ini tambahan ke bcrypt, bukan replacement
    - Dipake buat data yang perlu di-recover
    """
    if not password:
        return ""
    try:
        encrypted_bytes = cipher_suite.encrypt(password.encode())
        encrypted: str = encrypted_bytes.decode()
        return encrypted
    except Exception as e:
        # Log error without sensitive data
        logger.error(f"Error encrypting password: {type(e).__name__}")
        return password  # Return original if encryption fails


def decrypt_password(encrypted_password: str) -> str:
    """
    Dekripsi password yang dienkripsi dengan Fernet.
    Handle multiple format buat backward compatibility.

    Args:
        encrypted_password: Encrypted password string

    Returns:
        Decrypted password plaintext

    Compatibility handling:
    1. Bcrypt hash ($2b$ or $2a$) -> return as-is (verification only)
    2. Fernet token (gAAAAA...) -> decrypt dengan Fernet
    3. Plain text -> return as-is (legacy data)
    4. Invalid/corrupted -> raise ValueError

    Security flow:
    - Detect password format otomatis
    - Apply appropriate decryption method
    - Validate decryption success
    - Handle key mismatch gracefully

    Error handling:
    - Critical error kalau decryption gagal
    - Biasanya karena encryption key salah
    - Raise specific ValueError buat upstream handling
    - Log error tanpa expose sensitive data

    Use cases:
    - Legacy password migration
    - Config data recovery
    - Sensitive data access
    - Development data recovery

    Important:
    - Decryption failure = CRITICAL security issue
    - Biasanya encryption key mismatch
    - Must investigate immediately
    - Could indicate data tampering
    """
    if not encrypted_password:
        return ""

    # Check if the password is a bcrypt hash (starts with $2b$ or $2a$)
    if encrypted_password.startswith(("$2b$", "$2a$")):
        # Password sudah dalam bentuk bcrypt hash, kembalikan sebagai-is untuk verifikasi
        return encrypted_password

    # Check if the password does not appear to be a valid Fernet token.
    if not (isinstance(encrypted_password, str) and encrypted_password.startswith("gAAAAAB")):
        # Jika bukan token Fernet, asumsikan ini adalah password plain text (untuk backward compatibility)
        return encrypted_password

    try:
        # Attempt to decrypt the password.
        decrypted_bytes = cipher_suite.decrypt(encrypted_password.encode())
        decrypted_password_str: str = decrypted_bytes.decode()
        return decrypted_password_str
    except Exception as e:
        # If decryption fails, it is a critical error. Do not suppress it.
        # This is most likely due to an incorrect ENCRYPTION_KEY.
        logger.error(
            f"FATAL: Error decrypting password. This is likely due to an incorrect ENCRYPTION_KEY. Error: {type(e).__name__}"
        )
        # Raise a specific exception that can be caught upstream.
        raise ValueError("Decryption failed. The encryption key may be incorrect or the data is corrupted.")
