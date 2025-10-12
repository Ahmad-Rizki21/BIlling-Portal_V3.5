import re
from typing import Optional

from pydantic import BaseModel, Field, validator


class PaketLayananBase(BaseModel):
    id_brand: str = Field(..., min_length=1, max_length=50, description="ID brand paket layanan")
    nama_paket: str = Field(..., min_length=3, max_length=100, description="Nama paket layanan")
    kecepatan: int = Field(..., gt=0, le=10000, description="Kecepatan internet (Mbps)")
    harga: float = Field(..., gt=0, description="Harga paket per bulan")

    @validator("id_brand", pre=True)
    def validate_id_brand(cls, v):
        if v is None:
            raise ValueError("ID brand tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("ID brand tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("ID brand terlalu panjang (maksimal 50 karakter)")

        return v_str

    @validator("nama_paket", pre=True)
    def validate_nama_paket(cls, v):
        if v is None:
            raise ValueError("Nama paket tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama paket tidak boleh kosong")

        if len(v_str) < 3:
            raise ValueError("Nama paket harus minimal 3 karakter")

        if len(v_str) > 100:
            raise ValueError("Nama paket terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9\s\-\_\.\+\(\)]+$", v_str):
            raise ValueError("Nama paket hanya boleh mengandung huruf, angka, spasi, dan karakter khusus (-_+.())")

        return v_str

    @validator("kecepatan", pre=True)
    def validate_kecepatan(cls, v):
        if v is None:
            raise ValueError("Kecepatan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Kecepatan harus berupa angka")

        if v_int <= 0:
            raise ValueError("Kecepatan harus lebih besar dari 0")

        if v_int > 10000:
            raise ValueError("Kecepatan terlalu tinggi (maksimal 10000 Mbps)")

        return v_int

    @validator("harga", pre=True)
    def validate_harga(cls, v):
        if v is None:
            raise ValueError("Harga tidak boleh kosong")

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Harga harus berupa angka")

        if v_float <= 0:
            raise ValueError("Harga harus lebih besar dari 0")

        # Round to 2 decimal places
        return round(v_float, 2)


class PaketLayananCreate(PaketLayananBase):
    pass


class PaketLayananUpdate(BaseModel):
    nama_paket: Optional[str] = Field(None, min_length=3, max_length=100, description="Nama paket layanan")
    kecepatan: Optional[int] = Field(None, gt=0, le=10000, description="Kecepatan internet (Mbps)")
    harga: Optional[float] = Field(None, gt=0, description="Harga paket per bulan")

    @validator("nama_paket", pre=True)
    def validate_nama_paket_update(cls, v):
        if v is None:
            return v

        v_str = str(v).strip()
        if not v_str:
            return None  # Allow clearing the field

        if len(v_str) < 3:
            raise ValueError("Nama paket harus minimal 3 karakter")

        if len(v_str) > 100:
            raise ValueError("Nama paket terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9\s\-\_\.\+\(\)]+$", v_str):
            raise ValueError("Nama paket hanya boleh mengandung huruf, angka, spasi, dan karakter khusus (-_+.())")

        return v_str

    @validator("kecepatan", pre=True)
    def validate_kecepatan_update(cls, v):
        if v is None:
            return v

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Kecepatan harus berupa angka")

        if v_int <= 0:
            raise ValueError("Kecepatan harus lebih besar dari 0")

        if v_int > 10000:
            raise ValueError("Kecepatan terlalu tinggi (maksimal 10000 Mbps)")

        return v_int

    @validator("harga", pre=True)
    def validate_harga_update(cls, v):
        if v is None:
            return v

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Harga harus berupa angka")

        if v_float <= 0:
            raise ValueError("Harga harus lebih besar dari 0")

        # Round to 2 decimal places
        return round(v_float, 2)


class PaketLayanan(PaketLayananBase):
    id: int

    class Config:
        from_attributes = True
