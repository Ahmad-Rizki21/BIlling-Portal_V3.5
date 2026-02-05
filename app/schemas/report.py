from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime


# Skema sederhana untuk setiap baris invoice dalam tabel laporan
class InvoiceReportItem(BaseModel):
    invoice_number: str
    pelanggan_nama: str
    paid_at: Optional[datetime] = None
    total_harga: float
    metode_pembayaran: Optional[str] = None
    alamat: Optional[str] = None
    id_brand: Optional[str] = None

    class Config:
        from_attributes = True

# --- New Schemas for Billing Radius Style Report ---

class FinancialSummary(BaseModel):
    total_pemasukan: float
    total_pengeluaran: float
    saldo_akhir: float

class BillStat(BaseModel):
    count: int
    nominal: float
    diskon: float
    biaya_pasang: float
    total: float

class BillingSummary(BaseModel):
    total_tagihan: BillStat
    lunas: BillStat
    pending: BillStat
    telat: BillStat

class TaxStat(BaseModel):
    ppn: float
    bhp: float
    uso: float
    total_pajak: float

class TaxSummary(BaseModel):
    total: TaxStat
    lunas: TaxStat
    pending: TaxStat
    telat: TaxStat

class PaymentMethodStat(BaseModel):
    method: str
    count: int
    total_amount: float # Renamed from amount for clarity
    pajak: float
    diskon: float

# Skema utama untuk respons dari API laporan pendapatan
class RevenueReportResponse(BaseModel):
    total_pendapatan: float # Legacy
    total_invoices: int # Legacy
    
    financial_summary: Optional[FinancialSummary] = None
    billing_summary: Optional[BillingSummary] = None
    tax_summary: Optional[TaxSummary] = None
    payment_methods: List[PaymentMethodStat] = []

    rincian_invoice: List[InvoiceReportItem] # Legacy, might be empty
