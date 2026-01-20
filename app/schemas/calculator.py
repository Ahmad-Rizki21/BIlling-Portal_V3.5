# app/schemas/calculator.py
from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class ProrateCalculationRequest(BaseModel):
    id_brand: str
    paket_layanan_id: int
    tgl_mulai: date
    include_ppn_next_month: bool = False


class ProrateCalculationResponse(BaseModel):
    harga_dasar_prorate: float
    pajak: float
    total_harga_prorate: float
    periode_hari: int
    harga_bulan_depan: float | None = None
    ppn_bulan_depan: float | None = None
    total_bulan_depan_dengan_ppn: float | None = None
    total_keseluruhan: float | None = None


class DiskonCalculationRequest(BaseModel):
    """Request untuk kalkulator diskon"""
    id_brand: str = Field(..., description="ID brand / harga layanan")
    paket_layanan_id: int = Field(..., description="ID paket layanan")
    persentase_diskon: float = Field(..., gt=0, le=100, description="Persentase diskon (0-100)")


class DiskonCalculationResponse(BaseModel):
    """Response dari kalkulator diskon"""
    # Info paket
    nama_paket: str = Field(..., description="Nama paket layanan")
    nama_brand: str = Field(..., description="Nama brand")

    # Harga dasar
    harga_paket: float = Field(..., description="Harga paket dasar")
    pajak_persen: float = Field(..., description="Persentase pajak")
    pajak_amount: float = Field(..., description="Nominal pajak")
    subtotal_sebelum_diskon: float = Field(..., description="Subtotal sebelum diskon (harga paket + pajak)")

    # Diskon
    persentase_diskon: float = Field(..., description="Persentase diskon yang diterapkan")
    diskon_amount: float = Field(..., description="Nominal diskon")

    # Harga final
    harga_final: float = Field(..., description="Harga final setelah diskon")

    # Detail perhitungan (untuk transparency)
    detail_perhitungan: str = Field(..., description="Penjelasan detail perhitungan")
