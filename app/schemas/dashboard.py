from pydantic import BaseModel
from typing import List, Optional

# Skema BARU untuk setiap item pendapatan brand
class BrandRevenueItem(BaseModel):
    brand: str
    revenue: float

# Skema pendapatan yang diperbarui
class RevenueSummary(BaseModel):
    total: float
    periode: str
    breakdown: List[BrandRevenueItem] # Menggunakan list dinamis

# (Sisa skema lain seperti StatCard, ChartData, dll. tetap sama)
class StatCard(BaseModel):
    title: str
    value: str | int
    description: str

class ChartData(BaseModel):
    labels: List[str]
    data: List[int]

class InvoiceSummary(BaseModel):
    labels: List[str]
    total: List[int]
    lunas: List[int]
    menunggu: List[int]
    kadaluarsa: List[int]

class ChartData(BaseModel):
    labels: List[str]
    data: List[int]

class LoyalitasUserDetail(BaseModel):
    id: Optional[int] = None
    nama: Optional[str] = None
    id_pelanggan: Optional[str] = None
    alamat: Optional[str] = None
    no_telp: Optional[str] = None

# Skema utama yang menggabungkan semua data
class DashboardData(BaseModel):
    revenue_summary: Optional[RevenueSummary] = None
    stat_cards: List[StatCard] = []
    lokasi_chart: Optional[ChartData] = None
    paket_chart: Optional[ChartData] = None
    growth_chart: Optional[ChartData] = None
    invoice_summary_chart: Optional[InvoiceSummary] = None
    status_langganan_chart: Optional[ChartData] = None
    pelanggan_per_alamat_chart: Optional[ChartData] = None
    loyalitas_pembayaran_chart: Optional[ChartData] = None
    
    class Config:
        from_attributes = True