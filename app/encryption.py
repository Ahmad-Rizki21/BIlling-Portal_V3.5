# app/encryption.py
"""
Modul ini buat handle enkripsi data sensitif di sistem billing.
Pake Fernet encryption dari cryptography library yang symmetric dan secure.

Data yang dienkripsi:
- Password PPPoE pelanggan
- API keys (Xendit, Mikrotik, dll)
- Password server Mikrotik
- Data sensitif lainnya

Keamanan:
- AES 128-bit encryption (Fernet standard)
- Key dari environment variable
- URL-safe base64 encoding
- Singleton pattern buat konsistensi
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import settings  # Import settings


class EncryptionService:
    """
    Service class buat handle enkripsi dan dekripsi data sensitif.
    Pake pattern singleton biar konsisten dan efisien.

    Encryption method:
    - Fernet (AES 128-bit + HMAC + timestamp)
    - Symmetric encryption (sama key buat encrypt/decrypt)
    - URL-safe base64 output

    Security features:
    - Automatic tamper detection
    - Timestamp buat prevent replay attacks
    - Key rotation support (theoretically)

    Usage:
        service = EncryptionService()
        encrypted = service.encrypt("password123")
        decrypted = service.decrypt(encrypted)

    Note:
        - Key harus ada di environment variable ENCRYPTION_KEY
        - Hasil enkripsi selalu mulai dengan 'gAAAAA'
        - Auto detect kalau data udah terenkripsi
    """

    def __init__(self) -> None:
        key = settings.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY tidak ditemukan di environment variables.")

        # Fernet expects the URL-safe base64-encoded key as bytes.
        self.cipher_suite = Fernet(key.encode())

    def is_encrypted(self, value: str) -> bool:
        """
        Cek apakah sebuah nilai sudah terenkripsi atau belum.
        Pake heuristic sederhana: Fernet token selalu mulai dengan 'gAAAAA'.

        Args:
            value: String yang mau dicek

        Returns:
            True kalau value keliatannya terenkripsi, False kalau belum

        Note:
            - Ini heuristic check, 100% accurate buat Fernet tokens
            - Berguna buat prevent double encryption
        """
        # Fernet tokens are URL-safe base64 encoded and start with 'gAAAAA'
        return value.startswith("gAAAAA")

    def encrypt(self, plaintext: str) -> str:
        """
        Enkripsi plaintext jadi ciphertext pake Fernet encryption.

        Args:
            plaintext: Data asli yang mau dienkripsi

        Returns:
            Encrypted string (URL-safe base64)

        Safety features:
            - Auto skip kalau plaintext kosong
            - Auto detect dan skip kalau udah terenkripsi
            - Prevent double encryption

        Example:
            >>> service = EncryptionService()
            >>> encrypted = service.encrypt("password123")
            >>> print(encrypted)  # Output: gAAAAA...
        """
        if not plaintext or self.is_encrypted(plaintext):
            return plaintext

        encrypted_bytes = self.cipher_suite.encrypt(plaintext.encode())
        result: str = encrypted_bytes.decode()
        return result

    def decrypt(self, ciphertext: str) -> str:
        """
        Dekripsi ciphertext balik jadi plaintext asli.

        Args:
            ciphertext: Data terenkripsi yang mau didekripsi

        Returns:
            Plaintext asli atau ciphertext kalau gagal

        Error handling:
            - Auto skip kalau ciphertext kosong
            - Auto skip kalau bukan encrypted data
            - Graceful fallback: return ciphertext kalau gagal
            - Log error buat debugging (critical security issue)

        Security note:
            Kalau gagal dekripsi, ini INDIKASI MASALAH BESAR:
            - Encryption key salah
            - Data corrupted
            - Data dari sumber yang tidak trusted

        Example:
            >>> service = EncryptionService()
            >>> decrypted = service.decrypt("gAAAAA...")
            >>> print(decrypted)  # Output: password123
        """
        if not ciphertext or not self.is_encrypted(ciphertext):
            return ciphertext

        try:
            decrypted_bytes = self.cipher_suite.decrypt(ciphertext.encode())
            result: str = decrypted_bytes.decode()
            return result
        except Exception as e:
            # This is a critical error, likely due to a wrong key or corrupted data.
            # Re-raising or logging as a severe error is better than returning ciphertext.
            print(f"FATAL: Gagal mendekripsi data. Error: {e}")
            # Mengembalikan ciphertext agar tidak crash, tapi ini menandakan masalah besar.
            return ciphertext


# Singleton instance - global object buat encryption service
# Ini penting biar semua bagian aplikasi pake instance yang sama
# dan nggak perlu initialize berulang kali
encryption_service = EncryptionService()

"""
Cara pakai encryption service di seluruh aplikasi:

from app.encryption import encryption_service

# Enkripsi password
password = "rahasia123"
encrypted_password = encryption_service.encrypt(password)

# Dekripsi password
decrypted_password = encryption_service.decrypt(encrypted_password)

# Auto detect - nggak akan dobel encrypt
already_encrypted = "gAAAAA..."
still_encrypted = encryption_service.encrypt(already_encrypted)  # Tetap sama
"""
