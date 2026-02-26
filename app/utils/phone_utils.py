# app/utils/phone_utils.py
"""
Utility untuk normalisasi nomor telepon Indonesia.
Mendukung semua format input: 08xx, 62xx, +62xx, 8xx
dan menghasilkan format yang konsisten untuk Xendit API.
"""

from typing import Optional


def normalize_phone_for_xendit(phone: Optional[str]) -> str:
    """
    Normalisasi nomor telepon ke format internasional +62 untuk Xendit API.

    Mendukung semua format input:
    - '08131349588'    -> '+628131349588'   (format lokal 08)
    - '6281283725103'  -> '+6281283725103'  (format 62 tanpa +)
    - '+6281283725103' -> '+6281283725103'  (sudah benar)
    - '82124650465'    -> '+6282124650465'  (langsung 8 tanpa prefix)
    - '8131349588'     -> '+628131349588'   (langsung 8 tanpa prefix)

    Args:
        phone: Nomor telepon dalam format apapun

    Returns:
        Nomor telepon dalam format +62xxx untuk Xendit API.
        String kosong jika input kosong/None.
    """
    if not phone or not phone.strip():
        return ""

    # Bersihkan: hanya ambil digit (buang +, spasi, dash, dll)
    digits = ''.join(c for c in phone.strip() if c.isdigit())

    if not digits:
        return ""

    # Case 1: Sudah ada prefix 62 di depan (dari format 62xxx atau +62xxx)
    if digits.startswith('62') and len(digits) > 4:
        return f"+{digits}"

    # Case 2: Format lokal 0xxx (contoh 08131349588)
    if digits.startswith('0'):
        return f"+62{digits[1:]}"

    # Case 3: Langsung angka tanpa prefix (contoh 82124650465, 8131349588)
    # Asumsi: ini adalah nomor Indonesia tanpa country code
    return f"+62{digits}"


def normalize_phone_display(phone: Optional[str]) -> str:
    """
    Normalisasi nomor telepon ke format display 62xxx (tanpa +).
    Digunakan untuk tampilan di UI/response API.

    Args:
        phone: Nomor telepon dalam format apapun

    Returns:
        Nomor telepon dalam format 62xxx (tanpa +).
        String asli jika input kosong.
    """
    if not phone or not phone.strip():
        return phone or ""

    # Bersihkan: hanya ambil digit
    digits = ''.join(c for c in phone.strip() if c.isdigit())

    if not digits:
        return phone

    # Case 1: Sudah ada prefix 62
    if digits.startswith('62') and len(digits) > 4:
        return digits

    # Case 2: Format lokal 0xxx
    if digits.startswith('0'):
        return f"62{digits[1:]}"

    # Case 3: Langsung angka tanpa prefix
    return f"62{digits}"
