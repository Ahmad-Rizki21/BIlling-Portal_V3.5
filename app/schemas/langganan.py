import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, computed_field, validator

from .paket_layanan import PaketLayanan


class PaketLayananInLangganan(BaseModel):
    harga: float = Field(..., gt=0, description="Harga paket layanan")

    class Config:
        from_attributes = True

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

        return round(v_float, 2)


class HargaLayananInPelanggan(BaseModel):
    pajak: float = Field(..., ge=0, le=100, description="Persentase pajak (0-100%)")

    class Config:
        from_attributes = True

    @validator("pajak", pre=True)
    def validate_pajak(cls, v):
        if v is None:
            raise ValueError("Pajak tidak boleh kosong")

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Pajak harus berupa angka")

        if v_float < 0:
            raise ValueError("Pajak tidak boleh negatif")

        if v_float > 100:
            raise ValueError("Pajak tidak boleh lebih dari 100%")

        return v_float


class PelangganInLangganan(BaseModel):
    id: int = Field(..., gt=0, description="ID pelanggan")
    nama: str = Field(..., min_length=1, max_length=100, description="Nama pelanggan")
    alamat: str = Field(..., min_length=1, max_length=200, description="Alamat pelanggan")
    harga_layanan: Optional[HargaLayananInPelanggan] = None

    class Config:
        from_attributes = True

    @validator("id", pre=True)
    def validate_id(cls, v):
        if v is None:
            raise ValueError("ID pelanggan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih besar dari 0")

        return v_int

    @validator("nama", pre=True)
    def validate_nama(cls, v):
        if v is None:
            raise ValueError("Nama pelanggan tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama pelanggan tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nama pelanggan terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("alamat", pre=True)
    def validate_alamat(cls, v):
        if v is None:
            raise ValueError("Alamat pelanggan tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat pelanggan tidak boleh kosong")

        if len(v_str) > 200:
            raise ValueError("Alamat pelanggan terlalu panjang (maksimal 200 karakter)")

        return v_str


# -- Base Schema --
# Berisi field yang sama persis dengan kolom di database
class LanggananBase(BaseModel):
    pelanggan_id: int = Field(..., gt=0, description="ID pelanggan")
    paket_layanan_id: int = Field(..., gt=0, description="ID paket layanan")
    metode_pembayaran: str = Field(..., max_length=50, description="Metode pembayaran")
    harga_awal: Optional[float] = Field(None, ge=0, description="Harga awal langganan")
    status: str = Field(..., max_length=50, description="Status langganan")
    tgl_jatuh_tempo: Optional[date] = Field(None, description="Tanggal jatuh tempo")
    tgl_invoice_terakhir: Optional[date] = Field(None, description="Tanggal invoice terakhir")
    tgl_mulai_langganan: Optional[date] = Field(None, description="Tanggal mulai langganan")

    @validator("pelanggan_id", pre=True)
    def validate_pelanggan_id(cls, v):
        if v is None:
            raise ValueError("ID pelanggan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih besar dari 0")

        return v_int

    @validator("paket_layanan_id", pre=True)
    def validate_paket_layanan_id(cls, v):
        if v is None:
            raise ValueError("ID paket layanan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID paket layanan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID paket layanan harus lebih besar dari 0")

        return v_int

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran(cls, v):
        if v is None:
            raise ValueError("Metode pembayaran tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Metode pembayaran tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        # Valid payment methods
        valid_methods = ["Otomatis", "Prorate"]
        if v_str not in valid_methods:
            raise ValueError(f"Metode pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")

        return v_str

    @validator("harga_awal", pre=True)
    def validate_harga_awal(cls, v):
        if v is None or v == "":
            return None

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Harga awal harus berupa angka")

        if v_float < 0:
            raise ValueError("Harga awal tidak boleh negatif")

        return round(v_float, 2)

    @validator("status", pre=True)
    def validate_status(cls, v):
        if v is None:
            raise ValueError("Status tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Status tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Status terlalu panjang (maksimal 50 karakter)")

        # Valid statuses
        valid_statuses = ["Aktif", "Suspended", "Berhenti"]
        if v_str not in valid_statuses:
            raise ValueError(f"Status tidak valid. Pilihan yang tersedia: {', '.join(valid_statuses)}")

        return v_str


# -- Schema untuk Membuat Langganan Baru --
class LanggananCreate(BaseModel):
    pelanggan_id: int = Field(..., gt=0, description="ID pelanggan")
    paket_layanan_id: int = Field(..., gt=0, description="ID paket layanan")
    status: str = Field(..., max_length=50, description="Status langganan")
    metode_pembayaran: str = Field(..., max_length=50, description="Metode pembayaran")
    tgl_mulai_langganan: Optional[date] = Field(None, description="Tanggal mulai langganan")
    sertakan_bulan_depan: bool = Field(False, description="Sertakan bulan depan dalam tagihan")

    @validator("pelanggan_id", pre=True)
    def validate_pelanggan_id_create(cls, v):
        if v is None:
            raise ValueError("ID pelanggan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih besar dari 0")

        return v_int

    @validator("paket_layanan_id", pre=True)
    def validate_paket_layanan_id_create(cls, v):
        if v is None:
            raise ValueError("ID paket layanan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID paket layanan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID paket layanan harus lebih besar dari 0")

        return v_int

    @validator("status", pre=True)
    def validate_status_create(cls, v):
        if v is None:
            raise ValueError("Status tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Status tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Status terlalu panjang (maksimal 50 karakter)")

        # Valid statuses
        valid_statuses = ["Aktif", "Suspended", "Berhenti"]
        if v_str not in valid_statuses:
            raise ValueError(f"Status tidak valid. Pilihan yang tersedia: {', '.join(valid_statuses)}")

        return v_str

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran_create(cls, v):
        if v is None:
            raise ValueError("Metode pembayaran tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Metode pembayaran tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        # Valid payment methods
        valid_methods = ["Otomatis", "Prorate"]
        if v_str not in valid_methods:
            raise ValueError(f"Metode pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")

        return v_str


# -- Schema untuk Update Langganan --
class LanggananUpdate(BaseModel):
    paket_layanan_id: Optional[int] = Field(None, gt=0, description="ID paket layanan")
    status: Optional[str] = Field(None, max_length=50, description="Status langganan")
    tgl_jatuh_tempo: Optional[date] = Field(None, description="Tanggal jatuh tempo")
    metode_pembayaran: Optional[str] = Field(None, max_length=50, description="Metode pembayaran")
    harga_awal: Optional[float] = Field(None, ge=0, description="Harga awal langganan")

    @validator("paket_layanan_id", pre=True)
    def validate_paket_layanan_id_update(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID paket layanan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID paket layanan harus lebih besar dari 0")

        return v_int

    @validator("status", pre=True)
    def validate_status_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Status terlalu panjang (maksimal 50 karakter)")

        # Valid statuses
        valid_statuses = ["Aktif", "Suspended", "Berhenti"]
        if v_str not in valid_statuses:
            raise ValueError(f"Status tidak valid. Pilihan yang tersedia: {', '.join(valid_statuses)}")

        return v_str

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        # Valid payment methods
        valid_methods = ["Otomatis", "Prorate"]
        if v_str not in valid_methods:
            raise ValueError(f"Metode pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")

        return v_str

    @validator("harga_awal", pre=True)
    def validate_harga_awal_update(cls, v):
        if v is None or v == "":
            return None

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Harga awal harus berupa angka")

        if v_float < 0:
            raise ValueError("Harga awal tidak boleh negatif")

        return round(v_float, 2)


# -- Schema untuk Import --
class LanggananImport(BaseModel):
    email_pelanggan: str = Field(..., description="Email pelanggan")
    id_brand: str = Field(..., max_length=50, description="ID brand")
    nama_paket_layanan: str = Field(..., max_length=100, description="Nama paket layanan")
    status: str = Field("Aktif", max_length=50, description="Status langganan")
    metode_pembayaran: str = Field("Otomatis", max_length=50, description="Metode pembayaran")
    tgl_jatuh_tempo: Optional[date] = Field(None, description="Tanggal jatuh tempo")

    @validator("email_pelanggan", pre=True)
    def validate_email_pelanggan(cls, v):
        if v is None:
            raise ValueError("Email pelanggan tidak boleh kosong")

        v_str = str(v).strip().lower()
        if not v_str:
            raise ValueError("Email pelanggan tidak boleh kosong")

        # Basic email format check
        if "@" not in v_str or "." not in v_str.split("@")[-1]:
            raise ValueError("Format email tidak valid")

        return v_str

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

    @validator("nama_paket_layanan", pre=True)
    def validate_nama_paket_layanan(cls, v):
        if v is None:
            raise ValueError("Nama paket layanan tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama paket layanan tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nama paket layanan terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("status", pre=True)
    def validate_status_import(cls, v):
        if v is None:
            v = "Aktif"

        v_str = str(v).strip()
        if not v_str:
            v_str = "Aktif"

        if len(v_str) > 50:
            raise ValueError("Status terlalu panjang (maksimal 50 karakter)")

        # Valid statuses
        valid_statuses = ["Aktif", "Suspended", "Berhenti"]
        if v_str not in valid_statuses:
            raise ValueError(f"Status tidak valid. Pilihan yang tersedia: {', '.join(valid_statuses)}")

        return v_str

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran_import(cls, v):
        if v is None:
            v = "Otomatis"

        v_str = str(v).strip()
        if not v_str:
            v_str = "Otomatis"

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        # Valid payment methods
        valid_methods = ["Otomatis", "Prorate"]
        if v_str not in valid_methods:
            raise ValueError(f"Metode pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")

        return v_str


# -- Schema Utama untuk Response API (HANYA ADA SATU INI) --
# Inilah skema yang digunakan untuk menampilkan data ke frontend
class Langganan(LanggananBase):
    id: int = Field(..., gt=0, description="ID langganan")
    # Pastikan relasi ini sudah benar dan di-load di router Anda
    paket_layanan: PaketLayananInLangganan
    pelanggan: PelangganInLangganan

    @computed_field
    @property
    def harga_final(self) -> float:
        """Menghitung harga final (paket + PPN) untuk ditampilkan."""

        # Jika data relasi tidak lengkap, tampilkan harga awal sebagai fallback
        if not self.paket_layanan or not self.pelanggan.harga_layanan:
            return self.harga_awal or 0.0

        harga_paket = self.paket_layanan.harga
        pajak_persen = self.pelanggan.harga_layanan.pajak

        harga_total = harga_paket * (1 + (pajak_persen / 100))

        return round(harga_total)

    class Config:
        from_attributes = True

    @validator("id", pre=True)
    def validate_id_response(cls, v):
        if v is None:
            raise ValueError("ID langganan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID langganan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID langganan harus lebih besar dari 0")

        return v_int
