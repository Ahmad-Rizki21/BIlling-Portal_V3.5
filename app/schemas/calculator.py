# app/schemas/calculator.py
from pydantic import BaseModel
from datetime import date


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
