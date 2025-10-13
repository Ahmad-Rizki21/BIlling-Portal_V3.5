import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .config import settings  # Import settings


class EncryptionService:
    def __init__(self) -> None:
        key = settings.ENCRYPTION_KEY
        if not key:
            raise ValueError("ENCRYPTION_KEY tidak ditemukan di environment variables.")

        # Fernet expects the URL-safe base64-encoded key as bytes.
        self.cipher_suite = Fernet(key.encode())

    def is_encrypted(self, value: str) -> bool:
        """Cek apakah sebuah nilai sepertinya sudah terenkripsi."""
        if not isinstance(value, str):
            return False
        # Fernet tokens are URL-safe base64 encoded and start with 'gAAAAA'
        return value.startswith("gAAAAA")

    def encrypt(self, plaintext: str) -> str:
        """Enkripsi plaintext menjadi ciphertext"""
        if not plaintext or self.is_encrypted(plaintext):
            return plaintext

        encrypted_bytes = self.cipher_suite.encrypt(plaintext.encode())
        return encrypted_bytes.decode()

    def decrypt(self, ciphertext: str) -> str:
        """Dekripsi ciphertext menjadi plaintext"""
        if not ciphertext or not self.is_encrypted(ciphertext):
            return ciphertext

        try:
            decrypted_bytes = self.cipher_suite.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            # This is a critical error, likely due to a wrong key or corrupted data.
            # Re-raising or logging as a severe error is better than returning ciphertext.
            print(f"FATAL: Gagal mendekripsi data. Error: {e}")
            # Mengembalikan ciphertext agar tidak crash, tapi ini menandakan masalah besar.
            return ciphertext


# Singleton instance
encryption_service = EncryptionService()
