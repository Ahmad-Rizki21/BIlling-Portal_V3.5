from cryptography.fernet import Fernet
from .config import settings
import base64
import logging

logger = logging.getLogger(__name__)


# Inisialisasi cipher suite dengan kunci rahasia dari file config Anda
def get_cipher_suite():
    """Get cipher suite with proper key handling"""
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
    """Mengenkripsi password teks biasa."""
    if not password:
        return ""
    try:
        encrypted = cipher_suite.encrypt(password.encode()).decode()
        return encrypted
    except Exception as e:
        # Log error without sensitive data
        logger.error(f"Error encrypting password: {type(e).__name__}")
        return password  # Return original if encryption fails


def decrypt_password(encrypted_password: str) -> str:
    """Mendekripsi password yang sudah terenkripsi."""
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
        decrypted_password_str = decrypted_bytes.decode()
        return decrypted_password_str
    except Exception as e:
        # If decryption fails, it is a critical error. Do not suppress it.
        # This is most likely due to an incorrect ENCRYPTION_KEY.
        logger.error(
            f"FATAL: Error decrypting password. This is likely due to an incorrect ENCRYPTION_KEY. Error: {type(e).__name__}"
        )
        # Raise a specific exception that can be caught upstream.
        raise ValueError("Decryption failed. The encryption key may be incorrect or the data is corrupted.")
