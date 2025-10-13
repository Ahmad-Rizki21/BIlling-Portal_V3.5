import re
from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from .harga_layanan import HargaLayanan as HargaLayananSchema


# Skema untuk membuat Pelanggan baru
class PelangganCreate(BaseModel):
    no_ktp: str = Field(..., min_length=1, description="Nomor KTP (wajib)")
    nama: str = Field(..., min_length=1, description="Nama lengkap (wajib)")
    alamat: str = Field(..., min_length=1, description="Alamat utama (wajib)")
    alamat_2: Optional[str] = Field(None, description="Alamat tambahan (opsional)")
    tgl_instalasi: Optional[date] = Field(None, description="Tanggal instalasi (opsional)")
    blok: str = Field(..., min_length=1, description="Blok (wajib)")
    unit: str = Field(..., min_length=1, description="Unit (wajib)")
    no_telp: str = Field(..., min_length=1, description="Nomor telepon (wajib)")
    email: EmailStr = Field(..., description="Email (wajib)")
    id_brand: Optional[str] = Field(None, description="ID Brand (opsional)")
    layanan: Optional[str] = Field(None, description="Layanan (opsional)")

    @validator("no_ktp", pre=True)
    def validate_no_ktp(cls, v: Any) -> str:
        if v is None:
            raise ValueError("No KTP tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No KTP tidak boleh kosong")

        # Basic KTP format validation (16 digits)
        if not re.match(r"^\d{16}$", v_str):
            # If not exactly 16 digits, check if it's a reasonable length
            if len(v_str) < 10 or len(v_str) > 20:
                raise ValueError("No KTP harus berisi 10-20 karakter")

        return v_str

    @validator("nama", pre=True)
    def validate_nama(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Nama tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama tidak boleh kosong")

        if len(v_str) < 2:
            raise ValueError("Nama harus minimal 2 karakter")

        return v_str

    @validator("alamat", pre=True)
    def validate_alamat(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Alamat tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat tidak boleh kosong")

        if len(v_str) < 5:
            raise ValueError("Alamat harus minimal 5 karakter")

        return v_str

    @validator("blok", pre=True)
    def validate_blok(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Blok tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Blok tidak boleh kosong")

        return v_str

    @validator("unit", pre=True)
    def validate_unit(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Unit tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Unit tidak boleh kosong")

        return v_str

    @validator("no_telp", pre=True)
    def validate_no_telp(cls, v: Any) -> str:
        if v is None:
            raise ValueError("No Telepon tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No Telepon tidak boleh kosong")

        # Clean phone number (remove spaces, dashes, etc.)
        clean_phone = re.sub(r"[^\d+]", "", v_str)

        # Basic phone validation
        if len(clean_phone) < 8:
            raise ValueError("No Telepon terlalu pendek (minimal 8 digit)")

        if len(clean_phone) > 15:
            raise ValueError("No Telepon terlalu panjang (maksimal 15 digit)")

        return clean_phone

    @validator("email", pre=True)
    def validate_email_format(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Email tidak boleh kosong")

        v_str = str(v).strip().lower()
        if not v_str:
            raise ValueError("Email tidak boleh kosong")

        # Basic email format check before EmailStr validation
        if "@" not in v_str or "." not in v_str.split("@")[-1]:
            raise ValueError("Format email tidak valid")

        return v_str

    @validator("alamat_2", pre=True, always=True)
    def validate_alamat_2(cls, v: Any) -> Optional[str]:
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("id_brand", pre=True, always=True)
    def validate_id_brand(cls, v: Any) -> Optional[str]:
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("layanan", pre=True, always=True)
    def validate_layanan(cls, v: Any) -> Optional[str]:
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("tgl_instalasi", pre=True, always=True)
    def validate_tgl_instalasi(cls, v: Any) -> Optional[date]:
        if v is None or v == "":
            return None

        # If it's already a date object, return it
        if isinstance(v, date):
            return v

        # This will be handled in the route for CSV parsing
        return v

    class Config:
        from_attributes = True
        # Allow extra validation
        validate_assignment = True
        # Ensure JSON schema generation
        schema_extra = {
            "example": {
                "no_ktp": "1234567890123456",
                "nama": "John Doe",
                "alamat": "Jl. Example No. 123",
                "alamat_2": "RT 01 RW 02",
                "blok": "A",
                "unit": "12",
                "no_telp": "081234567890",
                "email": "john.doe@example.com",
                "tgl_instalasi": "2024-01-15",
                "id_brand": "BRAND001",
                "layanan": "Internet",
            }
        }


# Skema untuk menampilkan data Pelanggan
class Pelanggan(PelangganCreate):
    id: int
    harga_layanan: Optional[HargaLayananSchema] = None


class PelangganInLangganan(BaseModel):
    id: int
    nama: str
    alamat: str

    class Config:
        from_attributes = True


# Skema untuk pembaruan parsial (semua field opsional)
class PelangganUpdate(BaseModel):
    no_ktp: Optional[str] = None
    nama: Optional[str] = None
    alamat: Optional[str] = None
    alamat_2: Optional[str] = None
    tgl_instalasi: Optional[date] = None
    blok: Optional[str] = None
    unit: Optional[str] = None
    no_telp: Optional[str] = None
    email: Optional[EmailStr] = None
    id_brand: Optional[str] = None
    layanan: Optional[str] = None

    # Apply same validators for update, but only when values are provided
    @validator("no_ktp", pre=True)
    def validate_no_ktp_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return v
        return PelangganCreate.validate_no_ktp(v)

    @validator("nama", pre=True)
    def validate_nama_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return v
        return PelangganCreate.validate_nama(v)

    # Add other validators as needed...

    class Config:
        from_attributes = True
