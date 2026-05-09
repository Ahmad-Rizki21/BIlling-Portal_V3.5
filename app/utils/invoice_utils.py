# app/utils/invoice_utils.py
"""
Utility function untuk generate alamat singkat pada nomor invoice.
Khusus menangani lokasi Pulogebang yang memiliki format spesial:
- PG Blok: "PGBlok{huruf_blok}{unit}" (contoh: PGBlokA315)
- PG Tower: "PGTower{unit}" (contoh: PGTower1002)

Lokasi lain tetap menggunakan format lama (10 karakter pertama alamat yang di-sanitize).
"""

import re


def generate_alamat_singkat(alamat: str, blok: str = "", unit: str = "", max_len: int = 10) -> str:
    """
    Generate alamat singkat untuk nomor invoice.
    
    Khusus Pulogebang (Rusun Pulogebang / Pulo Gebang):
    - Jika blok = "Tower" → "PGTower{unit}"   (contoh: PGTower1002)
    - Jika blok = huruf  → "PGBlok{blok}{unit}" (contoh: PGBlokA315)
    
    Lokasi lain:
    - Sanitize alamat, uppercase, ambil max_len karakter pertama.
    
    Args:
        alamat: Alamat pelanggan (dari field pelanggan.alamat)
        blok: Blok pelanggan (dari field pelanggan.blok)
        unit: Unit pelanggan (dari field pelanggan.unit)
        max_len: Panjang maksimal untuk lokasi non-PG (default 10)
    
    Returns:
        String alamat singkat untuk digunakan di nomor invoice
    """
    alamat_lower = (alamat or "").lower()
    
    # Deteksi apakah ini lokasi Pulogebang
    is_pulogebang = any(keyword in alamat_lower for keyword in [
        "pulogebang", "pulo gebang", "pulog", "rusun pulogebang", "rusun pulo gebang"
    ])
    
    if is_pulogebang and blok:
        blok_clean = blok.strip()
        unit_clean = (unit or "").strip()
        
        if blok_clean.lower() == "tower":
            # PG Tower: PGTower{unit}
            return f"PGTower{unit_clean}"
        else:
            # PG Blok: PGBlok{huruf_blok}{unit}
            return f"PGBlok{blok_clean.upper()}{unit_clean}"
    
    # Default: sanitize alamat biasa (logika lama)
    return re.sub(r'[^a-zA-Z0-9]', '', alamat or '').upper()[:max_len]
