# app/routers/calculator.py
import math
from calendar import monthrange
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..schemas.calculator import ProrateCalculationRequest, ProrateCalculationResponse

router = APIRouter(prefix="/calculator", tags=["Calculator"])


@router.post("/prorate", response_model=ProrateCalculationResponse)
async def calculate_prorate_price(request: ProrateCalculationRequest, db: AsyncSession = Depends(get_db)):
    # 1. Ambil data paket dan brand dari database
    paket = await db.get(PaketLayananModel, request.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan")

    brand = await db.get(HargaLayananModel, request.id_brand)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")

    # 2. Lakukan logika perhitungan prorate
    start_date = request.tgl_mulai
    harga_paket = float(paket.harga)
    pajak_persen = float(brand.pajak)

    _, last_day_of_month = monthrange(start_date.year, start_date.month)
    remaining_days = last_day_of_month - start_date.day + 1

    if remaining_days < 0:
        remaining_days = 0

    harga_per_hari = harga_paket / last_day_of_month
    harga_dasar_prorate = harga_per_hari * remaining_days

    pajak_mentah = harga_dasar_prorate * (pajak_persen / 100)
    pajak = math.floor(pajak_mentah + 0.5)  # Pembulatan standar

    total_harga_prorate = round(harga_dasar_prorate + pajak, 0)

    return ProrateCalculationResponse(
        harga_dasar_prorate=round(harga_dasar_prorate, 0),
        pajak=pajak,
        total_harga_prorate=total_harga_prorate,
        periode_hari=remaining_days,
    )
