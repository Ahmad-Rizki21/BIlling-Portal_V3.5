from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel


# Skema sederhana untuk setiap baris invoice dalam tabel laporan
class InvoiceReportItem(BaseModel):
    invoice_number: str
    pelanggan_nama: str
    paid_at: datetime
    total_harga: float
    metode_pembayaran: Optional[str] = None
    alamat: Optional[str] = None
    id_brand: Optional[str] = None

    class Config:
        from_attributes = True


# Skema utama untuk respons dari API laporan pendapatan
class RevenueReportResponse(BaseModel):
    total_pendapatan: float
    total_invoices: int
    rincian_invoice: List[InvoiceReportItem]
