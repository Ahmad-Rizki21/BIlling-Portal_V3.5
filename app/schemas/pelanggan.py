from pydantic import BaseModel, EmailStr, validator, Field
from datetime import date
from typing import Optional, List
import re

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

    # Konfigurasi untuk memungkinkan nilai kosong pada field opsional
    class Config:  # type: ignore
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("no_ktp", pre=True)
    def validate_no_ktp(cls, v):
        if v is None:
            raise ValueError("No KTP tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No KTP tidak boleh kosong")

        # Izinkan nilai dummy tertentu untuk kompatibilitas backward
        dummy_ktp_values = [
            "0000000000000000",
            "0" * 16,
            "",
            " ",
            "N/A",
            "NULL",
            "None",
        ]
        if v_str in dummy_ktp_values:
            # Untuk nilai dummy, gunakan format yang konsisten
            return "0000000000000000"

        # Basic KTP format validation (16 digits)
        if not re.match(r"^\d{16}$", v_str):
            # If not exactly 16 digits, check if it's a reasonable length
            if len(v_str) < 10 or len(v_str) > 20:
                raise ValueError("No KTP harus berisi 10-20 karakter")

        return v_str

    @validator("nama", pre=True)
    def validate_nama(cls, v):
        if v is None:
            raise ValueError("Nama tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama tidak boleh kosong")

        if len(v_str) < 2:
            raise ValueError("Nama harus minimal 2 karakter")

        return v_str

    @validator("alamat", pre=True)
    def validate_alamat(cls, v):
        if v is None:
            raise ValueError("Alamat tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat tidak boleh kosong")

        if len(v_str) < 5:
            raise ValueError("Alamat harus minimal 5 karakter")

        return v_str

    @validator("blok", pre=True)
    def validate_blok(cls, v):
        if v is None:
            raise ValueError("Blok tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Blok tidak boleh kosong")

        return v_str

    @validator("unit", pre=True)
    def validate_unit(cls, v):
        if v is None:
            raise ValueError("Unit tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Unit tidak boleh kosong")

        return v_str

    @validator("no_telp", pre=True)
    def validate_no_telp(cls, v):
        if v is None:
            raise ValueError("No Telepon tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No Telepon tidak boleh kosong")

        # Check for forbidden characters (specifically dashes)
        if "-" in v_str:
            raise ValueError("No Telepon tidak boleh mengandung karakter '-' (dash). Gunakan hanya angka dan spasi.")

        # Clean phone number (remove spaces, but keep digits and +)
        clean_phone = re.sub(r"[^\d+]", "", v_str)

        # Basic phone validation
        if len(clean_phone) < 8:
            raise ValueError("No Telepon terlalu pendek (minimal 8 digit)")

        if len(clean_phone) > 15:
            raise ValueError("No Telepon terlalu panjang (maksimal 15 digit)")

        return clean_phone

    @validator("email", pre=True)
    def validate_email_format(cls, v):
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
    def validate_alamat_2(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("id_brand", pre=True, always=True)
    def validate_id_brand(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("layanan", pre=True, always=True)
    def validate_layanan(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("tgl_instalasi", pre=True, always=True)
    def validate_tgl_instalasi(cls, v):
        if v is None or v == "":
            return None

        # If it's already a date object, return it
        if isinstance(v, date):
            return v

        # Handle string dates
        if isinstance(v, str):
            if v.strip() == "":
                return None
            # This will be handled in the route for CSV parsing
            return v

        return v

    class Config:  # type: ignore
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
class Pelanggan(BaseModel):
    id: int
    no_ktp: str
    nama: str
    alamat: str
    alamat_2: Optional[str] = None
    tgl_instalasi: Optional[date] = None
    blok: str
    unit: str
    no_telp: str
    email: EmailStr
    id_brand: Optional[str] = None
    layanan: Optional[str] = None
    harga_layanan: Optional[HargaLayananSchema] = None

    class Config:  # type: ignore
        from_attributes = True


class PelangganInLangganan(BaseModel):
    id: int
    nama: str
    alamat: str

    class Config:  # type: ignore
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
    def validate_no_ktp_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_no_ktp(v)  # type: ignore

    @validator("nama", pre=True)
    def validate_nama_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_nama(v)  # type: ignore

    @validator("alamat", pre=True)
    def validate_alamat_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_alamat(v)  # type: ignore

    @validator("alamat_2", pre=True, always=True)
    def validate_alamat_2_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("blok", pre=True)
    def validate_blok_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_blok(v)  # type: ignore

    @validator("unit", pre=True)
    def validate_unit_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_unit(v)  # type: ignore

    @validator("no_telp", pre=True)
    def validate_no_telp_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_no_telp(v)  # type: ignore

    @validator("email", pre=True)
    def validate_email_update(cls, v):
        if v is None:
            return v
        return PelangganCreate.validate_email_format(v)  # type: ignore

    @validator("id_brand", pre=True, always=True)
    def validate_id_brand_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("layanan", pre=True, always=True)
    def validate_layanan_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("tgl_instalasi", pre=True, always=True)
    def validate_tgl_instalasi_update(cls, v):
        if v is None or v == "":
            return None

        # If it's already a date object, return it
        if isinstance(v, date):
            return v

        # Handle string dates
        if isinstance(v, str):
            if v.strip() == "":
                return None
            # This will be handled in the route for CSV parsing
            return v

        return v

    class Config:  # type: ignore
        from_attributes = True
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


# Skema untuk import data dari CSV
class PelangganImport(BaseModel):
    """
    Skema untuk validasi data pelanggan saat import dari CSV.
    Ini adalah versi yang lebih fleksibel dari PelangganCreate untuk menangani
    data yang mungkin tidak lengkap atau menggunakan nilai dummy.
    """

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
    def validate_no_ktp_import(cls, v):
        if v is None:
            raise ValueError("No KTP tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No KTP tidak boleh kosong")

        # Izinkan nilai dummy tertentu untuk kompatibilitas backward
        dummy_ktp_values = [
            "0000000000000000",
            "0" * 16,
            "",
            " ",
            "N/A",
            "NULL",
            "None",
        ]
        if v_str in dummy_ktp_values:
            # Untuk nilai dummy, gunakan format yang konsisten
            return "0000000000000000"

        # Basic KTP format validation (16 digits)
        if not re.match(r"^\d{16}$", v_str):
            # If not exactly 16 digits, check if it's a reasonable length
            if len(v_str) < 10 or len(v_str) > 20:
                raise ValueError("No KTP harus berisi 10-20 karakter")

        return v_str

    @validator("nama", pre=True)
    def validate_nama_import(cls, v):
        if v is None:
            raise ValueError("Nama tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama tidak boleh kosong")

        if len(v_str) < 2:
            raise ValueError("Nama harus minimal 2 karakter")

        return v_str

    @validator("alamat", pre=True)
    def validate_alamat_import(cls, v):
        if v is None:
            raise ValueError("Alamat tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat tidak boleh kosong")

        if len(v_str) < 5:
            raise ValueError("Alamat harus minimal 5 karakter")

        return v_str

    @validator("blok", pre=True)
    def validate_blok_import(cls, v):
        if v is None:
            raise ValueError("Blok tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Blok tidak boleh kosong")

        return v_str

    @validator("unit", pre=True)
    def validate_unit_import(cls, v):
        if v is None:
            raise ValueError("Unit tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Unit tidak boleh kosong")

        return v_str

    @validator("no_telp", pre=True)
    def validate_no_telp_import(cls, v):
        if v is None:
            raise ValueError("No Telepon tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("No Telepon tidak boleh kosong")

        # Check for forbidden characters (specifically dashes)
        if "-" in v_str:
            raise ValueError("No Telepon tidak boleh mengandung karakter '-' (dash). Gunakan hanya angka dan spasi.")

        # Clean phone number (remove spaces, but keep digits and +)
        clean_phone = re.sub(r"[^\d+]", "", v_str)

        # Basic phone validation
        if len(clean_phone) < 8:
            raise ValueError("No Telepon terlalu pendek (minimal 8 digit)")

        if len(clean_phone) > 15:
            raise ValueError("No Telepon terlalu panjang (maksimal 15 digit)")

        return clean_phone

    @validator("email", pre=True)
    def validate_email_format_import(cls, v):
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
    def validate_alamat_2_import(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("id_brand", pre=True, always=True)
    def validate_id_brand_import(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("layanan", pre=True, always=True)
    def validate_layanan_import(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if v_str == "" or v_str.lower() in ["null", "none", "nan"]:
            return None

        return v_str

    @validator("tgl_instalasi", pre=True, always=True)
    def validate_tgl_instalasi_import(cls, v):
        if v is None or v == "":
            return None

        # If it's already a date object, return it
        if isinstance(v, date):
            return v

        # Handle string dates
        if isinstance(v, str):
            if v.strip() == "":
                return None
            # This will be handled in the route for CSV parsing
            return v

        return v

    class Config:  # type: ignore
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
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


# Skema untuk pagination response
class PaginationInfo(BaseModel):
    totalItems: int = Field(..., ge=0, description="Total jumlah items dalam database")
    currentPage: int = Field(..., ge=1, description="Halaman saat ini")
    itemsPerPage: int = Field(..., ge=1, description="Jumlah items per halaman")
    totalPages: int = Field(..., ge=0, description="Total jumlah halaman")
    hasNext: bool = Field(..., description="Apakah ada halaman berikutnya")
    hasPrevious: bool = Field(..., description="Apakah ada halaman sebelumnya")
    startIndex: int = Field(..., ge=0, description="Index awal items saat ini")
    endIndex: int = Field(..., ge=0, description="Index akhir items saat ini")

    class Config:  # type: ignore
        from_attributes = True


# Skema response dengan pagination
class PaginatedPelangganResponse(BaseModel):
    data: List[Pelanggan] = Field(..., description="Daftar pelanggan")
    pagination: PaginationInfo = Field(..., description="Informasi pagination")
    meta: dict = Field(default_factory=dict, description="Metadata tambahan")

    class Config:  # type: ignore
        from_attributes = True


# ====================================================================
# SKEMA BARU: CEK IP ADDRESS
# ====================================================================


class IPCheckRequest(BaseModel):
    """Skema input untuk pengecekan IP address"""

    ip_address: str = Field(..., max_length=15, description="Alamat IP yang akan dicek")
    current_id: Optional[int] = Field(None, description="ID data teknis saat ini (untuk mode edit)")

    @validator("ip_address", pre=True)
    def validate_ip_address(cls, v):
        if v is None:
            raise ValueError("Alamat IP tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat IP tidak boleh kosong")

        if len(v_str) > 15:
            raise ValueError("Alamat IP terlalu panjang (maksimal 15 karakter)")

        # Basic IP validation
        ip_parts = v_str.split(".")
        if len(ip_parts) != 4:
            raise ValueError("Format IP tidak valid")

        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError("Format IP tidak valid")
            except ValueError:
                raise ValueError("Format IP tidak valid")

        return v_str

    @validator("current_id", pre=True)
    def validate_current_id(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID harus berupa angka")

        if v_int < 0:
            raise ValueError("ID tidak boleh negatif")

        return v_int


class IPCheckResponse(BaseModel):
    """Skema response untuk hasil pengecekan IP address"""

    is_taken: bool = Field(..., description="Apakah IP sudah digunakan")
    message: str = Field(..., description="Pesan hasil pengecekan")
    owner_id: Optional[str] = Field(None, description="ID PPPoE pemilik IP (jika ada)")

    @validator("message", pre=True)
    def validate_message(cls, v):
        if v is None:
            return ""

        v_str = str(v)
        if len(v_str) > 200:
            raise ValueError("Pesan terlalu panjang (maksimal 200 karakter)")

        return v_str

    @validator("owner_id", pre=True)
    def validate_owner_id(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("ID pemilik terlalu panjang (maksimal 100 karakter)")

        return v_str


# ====================================================================
# END OF FILE
# ====================================================================
