# app/schemas/calculator.py
from pydantic import BaseModel
from datetime import date


class ProrateCalculationRequest(BaseModel):
    id_brand: str
    paket_layanan_id: int
    tgl_mulai: date


class ProrateCalculationResponse(BaseModel):
    harga_dasar_prorate: float
    pajak: float
    total_harga_prorate: float
    periode_hari: int
