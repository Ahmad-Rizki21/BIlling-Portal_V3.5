from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import date, datetime
import re


# ===================================================================
# Skema Input (Request Body)
# ===================================================================


class InvoiceGenerate(BaseModel):
    """
    Skema input untuk men-trigger pembuatan invoice untuk sebuah langganan.
    Ini adalah satu-satunya data yang dibutuhkan dari user/frontend.
    """

    langganan_id: int = Field(..., gt=0, description="ID langganan yang akan dibuatkan invoice")

    @validator("langganan_id", pre=True)
    def validate_langganan_id(cls, v):
        if v is None:
            raise ValueError("ID langganan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID langganan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID langganan harus lebih besar dari 0")

        return v_int

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class InvoiceUpdate(BaseModel):
    """
    Skema untuk memperbarui invoice. Misalnya, setelah menerima callback dari Xendit.
    Semua field bersifat opsional.
    """

    status_invoice: Optional[str] = Field(None, max_length=50, description="Status invoice")
    payment_link: Optional[str] = Field(None, max_length=500, description="Link pembayaran")
    expiry_date: Optional[datetime] = Field(None, description="Tanggal kadaluarsa invoice")
    xendit_id: Optional[str] = Field(None, max_length=100, description="ID invoice di Xendit")
    xendit_external_id: Optional[str] = Field(None, max_length=200, description="External ID invoice di Xendit")
    paid_amount: Optional[float] = Field(None, ge=0, description="Jumlah pembayaran")
    paid_at: Optional[datetime] = Field(None, description="Waktu pembayaran")
    pelanggan_id: Optional[int] = Field(None, gt=0, description="ID pelanggan (harus > 0)")

    @validator("status_invoice", pre=True)
    def validate_status_invoice(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Status invoice terlalu panjang (maksimal 50 karakter)")

        # Valid status values
        valid_statuses = ["Belum Dibayar", "Lunas", "Kadaluarsa", "Dibatalkan"]
        if v_str not in valid_statuses:
            raise ValueError(f"Status invoice tidak valid. Pilihan yang tersedia: {', '.join(valid_statuses)}")

        return v_str

    @validator("payment_link", pre=True)
    def validate_payment_link(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 500:
            raise ValueError("Link pembayaran terlalu panjang (maksimal 500 karakter)")

        # Basic URL validation
        if not re.match(r"^https?://", v_str):
            raise ValueError("Link pembayaran harus berupa URL yang valid")

        return v_str

    @validator("xendit_id", pre=True)
    def validate_xendit_id(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("ID Xendit terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("xendit_external_id", pre=True)
    def validate_xendit_external_id(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 200:
            raise ValueError("External ID Xendit terlalu panjang (maksimal 200 karakter)")

        return v_str

    @validator("paid_amount", pre=True)
    def validate_paid_amount(cls, v):
        if v is None:
            return None

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Jumlah pembayaran harus berupa angka")

        if v_float < 0:
            raise ValueError("Jumlah pembayaran tidak boleh negatif")

        return round(v_float, 2)

    @validator("pelanggan_id", pre=True)
    def validate_pelanggan_id_update(cls, v):
        # Tambahkan validasi untuk mencegah pelanggan_id menjadi None/null
        # Jika ingin menghapus relasi, seharusnya tidak mengupdate pelanggan_id ke None
        # Tapi jika memang diperlukan, pastikan logikanya benar
        if v is None:
            # Jangan izinkan pelanggan_id menjadi None jika memang field ini wajib
            # Alternatif: Biarkan None jika memang boleh, tapi validasi di level database
            return v

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih besar dari 0")

        return v_int

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class MarkAsPaidRequest(BaseModel):
    """Skema input untuk menandai lunas secara manual."""

    metode_pembayaran: str = Field("Cash", max_length=50, description="Metode pembayaran")

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran(cls, v):
        if v is None:
            v = "Cash"

        v_str = str(v).strip()
        if not v_str:
            v_str = "Cash"

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        # Valid payment methods
        valid_methods = ["Cash", "Transfer Bank", "E-Wallet", "Lainnya"]
        if v_str not in valid_methods:
            raise ValueError(f"Metode pembayaran tidak valid. Pilihan yang tersedia: {', '.join(valid_methods)}")

        return v_str

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


# ===================================================================
# Skema Output (Response Body)
# ===================================================================


class InvoiceBase(BaseModel):
    """
    Skema dasar yang berisi field-field utama dari sebuah invoice.
    """

    invoice_number: str = Field(..., min_length=1, max_length=100, description="Nomor invoice")
    pelanggan_id: int = Field(..., gt=0, description="ID pelanggan")
    total_harga: float = Field(..., ge=0, description="Total harga invoice")
    tgl_invoice: date = Field(..., description="Tanggal pembuatan invoice")
    tgl_jatuh_tempo: date = Field(..., description="Tanggal jatuh tempo pembayaran")
    status_invoice: str = Field(..., max_length=50, description="Status invoice")
    metode_pembayaran: Optional[str] = Field(None, max_length=50, description="Metode pembayaran")

    @validator("invoice_number", pre=True)
    def validate_invoice_number(cls, v):
        if v is None:
            raise ValueError("Nomor invoice tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nomor invoice tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nomor invoice terlalu panjang (maksimal 100 karakter)")

        return v_str

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

    @validator("total_harga", pre=True)
    def validate_total_harga(cls, v):
        if v is None:
            raise ValueError("Total harga tidak boleh kosong")

        try:
            v_float = float(v)
        except (ValueError, TypeError):
            raise ValueError("Total harga harus berupa angka")

        if v_float < 0:
            raise ValueError("Total harga tidak boleh negatif")

        return round(v_float, 2)

    @validator("status_invoice", pre=True)
    def validate_status_invoice_base(cls, v):
        if v is None:
            raise ValueError("Status invoice tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Status invoice tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Status invoice terlalu panjang (maksimal 50 karakter)")

        return v_str

    @validator("metode_pembayaran", pre=True)
    def validate_metode_pembayaran_base(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Metode pembayaran terlalu panjang (maksimal 50 karakter)")

        return v_str

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class Invoice(InvoiceBase):
    """
    Skema lengkap untuk menampilkan data invoice sebagai respons dari API.
    Mencakup semua kolom dari tabel 'invoices'.
    """

    id: int
    id_pelanggan: str = Field(..., min_length=1, max_length=100, description="ID pelanggan di sistem teknis")
    brand: str = Field(..., min_length=1, max_length=100, description="Brand pelanggan")
    no_telp: str = Field(..., min_length=1, max_length=20, description="Nomor telepon pelanggan")
    email: EmailStr = Field(..., description="Email pelanggan")
    payment_link: Optional[str] = Field(None, max_length=500, description="Link pembayaran")
    expiry_date: Optional[datetime] = Field(None, description="Tanggal kadaluarsa invoice")
    xendit_id: Optional[str] = Field(None, max_length=100, description="ID invoice di Xendit")
    xendit_external_id: Optional[str] = Field(None, max_length=200, description="External ID invoice di Xendit")
    paid_amount: Optional[float] = Field(None, ge=0, description="Jumlah pembayaran")
    paid_at: Optional[datetime] = Field(None, description="Waktu pembayaran")
    created_at: Optional[datetime] = Field(None, description="Waktu pembuatan record")
    updated_at: Optional[datetime] = Field(None, description="Waktu update terakhir")

    # Tambahkan field computed untuk status link pembayaran
    payment_link_status: Optional[str] = Field(None, description="Status link pembayaran (Belum Dibayar/Expired/Lunas)")
    is_payment_link_active: Optional[bool] = Field(None, description="True jika link pembayaran masih aktif")

    class Config:
        from_attributes = True
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("id_pelanggan", pre=True)
    def validate_id_pelanggan(cls, v):
        if v is None:
            raise ValueError("ID pelanggan teknis tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("ID pelanggan teknis tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("ID pelanggan teknis terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("brand", pre=True)
    def validate_brand(cls, v):
        if v is None:
            raise ValueError("Brand tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Brand tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Brand terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("no_telp", pre=True)
    def validate_no_telp(cls, v):
        if v is None:
            raise ValueError("Nomor telepon tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nomor telepon tidak boleh kosong")

        if len(v_str) > 20:
            raise ValueError("Nomor telepon terlalu panjang (maksimal 20 karakter)")

        # Clean phone number
        clean_phone = re.sub(r"[^0-9\+]", "", v_str)
        return clean_phone
