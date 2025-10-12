# app/schemas/calculator.py
from datetime import date

from pydantic import BaseModel


class ProrateCalculationRequest(BaseModel):
    id_brand: str
    paket_layanan_id: int
    tgl_mulai: date


class ProrateCalculationResponse(BaseModel):
    harga_dasar_prorate: float
    pajak: float
    total_harga_prorate: float
    periode_hari: int
