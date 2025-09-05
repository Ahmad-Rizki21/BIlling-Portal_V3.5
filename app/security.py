from cryptography.fernet import Fernet
from .config import settings

# Inisialisasi cipher suite dengan kunci rahasia dari file config Anda
cipher_suite = Fernet(settings.ENCRYPTION_KEY.encode())

def encrypt_password(password: str) -> str:
    """Mengenkripsi password teks biasa."""
    if not password:
        return ""
    return cipher_suite.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    """Mendekripsi password yang sudah terenkripsi."""
    if not encrypted_password:
        return ""
    return cipher_suite.decrypt(encrypted_password.encode()).decode()