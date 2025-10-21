from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

# ===================================================================
# Skema Input (Request Body)
# ===================================================================


class InvoiceGenerate(BaseModel):
    """
    Skema input untuk men-trigger pembuatan invoice untuk sebuah langganan.
    Ini adalah satu-satunya data yang dibutuhkan dari user/frontend.
    """

    langganan_id: int


class InvoiceUpdate(BaseModel):
    """
    Skema untuk memperbarui invoice. Misalnya, setelah menerima callback dari Xendit.
    Semua field bersifat opsional.
    """

    status_invoice: Optional[str] = None
    payment_link: Optional[str] = None
    expiry_date: Optional[datetime] = None
    xendit_id: Optional[str] = None
    xendit_external_id: Optional[str] = None
    paid_amount: Optional[float] = None
    paid_at: Optional[datetime] = None


# ===================================================================
# Skema Output (Response Body)
# ===================================================================


class InvoiceBase(BaseModel):
    """
    Skema dasar yang berisi field-field utama dari sebuah invoice.
    """

    invoice_number: str
    pelanggan_id: int
    total_harga: float
    tgl_invoice: date
    tgl_jatuh_tempo: date
    status_invoice: str
    metode_pembayaran: Optional[str] = None


class Invoice(InvoiceBase):
    """
    Skema lengkap untuk menampilkan data invoice sebagai respons dari API.
    Mencakup semua kolom dari tabel 'invoices'.
    """

    id: int
    id_pelanggan: str
    brand: str
    no_telp: str
    email: EmailStr
    payment_link: Optional[str] = None
    expiry_date: Optional[datetime] = None
    xendit_id: Optional[str] = None
    xendit_external_id: Optional[str] = None
    paid_amount: Optional[float] = None
    paid_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarkAsPaidRequest(BaseModel):
    """Skema input untuk menandai lunas secara manual."""

    metode_pembayaran: str = "Cash"
