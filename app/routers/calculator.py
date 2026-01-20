# app/routers/calculator.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from calendar import monthrange
import math
import logging

from ..database import get_db
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..schemas.calculator import (
    ProrateCalculationRequest,
    ProrateCalculationResponse,
    DiskonCalculationRequest,
    DiskonCalculationResponse,
)

logger = logging.getLogger(__name__)
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

    # Logika untuk harga bulan depan dengan PPN
    harga_bulan_depan = None
    ppn_bulan_depan = None
    total_bulan_depan_dengan_ppn = None
    total_keseluruhan = None

    if request.include_ppn_next_month:
        harga_bulan_depan = harga_paket
        ppn_mentah_bulan_depan = harga_bulan_depan * (pajak_persen / 100)
        ppn_bulan_depan = math.floor(ppn_mentah_bulan_depan + 0.5)  # Pembulatan standar
        total_bulan_depan_dengan_ppn = round(harga_bulan_depan + ppn_bulan_depan, 0)
        total_keseluruhan = round(total_harga_prorate + total_bulan_depan_dengan_ppn, 0)

    return ProrateCalculationResponse(
        harga_dasar_prorate=round(harga_dasar_prorate, 0),
        pajak=pajak,
        total_harga_prorate=total_harga_prorate,
        periode_hari=remaining_days,
        harga_bulan_depan=harga_bulan_depan,
        ppn_bulan_depan=ppn_bulan_depan,
        total_bulan_depan_dengan_ppn=total_bulan_depan_dengan_ppn,
        total_keseluruhan=total_keseluruhan,
    )


@router.post("/diskon", response_model=DiskonCalculationResponse)
async def calculate_diskon_price(request: DiskonCalculationRequest, db: AsyncSession = Depends(get_db)):
    """
    Kalkulator Diskon - Menghitung harga setelah diskon.

    Perhitungan:
    1. Ambil harga paket dari database
    2. Tambahkan pajak (PPN)
    3. Hitung diskon dari subtotal
    4. Kurangi diskon dari subtotal

    Rumus:
    - pajak_amount = floor((harga_paket × pajak_persen / 100) + 0.5)
    - subtotal = harga_paket + pajak_amount
    - diskon_amount = floor((subtotal × persentase_diskon / 100) + 0.5)
    - harga_final = subtotal - diskon_amount
    """
    # 1. Ambil data paket dan brand dari database
    paket = await db.get(PaketLayananModel, request.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan")

    brand = await db.get(HargaLayananModel, request.id_brand)
    if not brand:
        raise HTTPException(status_code=404, detail="Brand tidak ditemukan")

    # 2. Ambil nilai dasar
    harga_paket = float(paket.harga)
    pajak_persen = float(brand.pajak)
    persentase_diskon = float(request.persentase_diskon)

    # 3. Hitung pajak (dengan pembulatan standar + 0.5)
    pajak_mentah = harga_paket * (pajak_persen / 100)
    pajak_amount = math.floor(pajak_mentah + 0.5)

    # 4. Hitung subtotal sebelum diskon
    subtotal_sebelum_diskon = harga_paket + pajak_amount

    # 5. Hitung diskon (dengan pembulatan standar + 0.5)
    diskon_mentah = subtotal_sebelum_diskon * (persentase_diskon / 100)
    diskon_amount = math.floor(diskon_mentah + 0.5)

    # 6. Hitung harga final
    harga_final = subtotal_sebelum_diskon - diskon_amount

    # 7. Buat detail perhitungan untuk transparency
    detail_perhitungan = f"""📊 Rincian Perhitungan Diskon:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 Harga Paket     : Rp {harga_paket:,.0f}
📈 Pajak ({pajak_persen:.0f}%)    : Rp {pajak_amount:,.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Subtotal        : Rp {subtotal_sebelum_diskon:,.0f}
🏷️  Diskon ({persentase_diskon:.0f}%)   : -Rp {diskon_amount:,.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Harga Final     : Rp {harga_final:,.0f}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💬 Catatan:
• Pajak dihitung dari harga paket
• Diskon dihitung dari subtotal (harga + pajak)
• Pembulatan menggunakan floor(x + 0.5)"""

    logger.info(f"💰 Diskon calculator: {paket.nama_paket} ({brand.brand}) - Diskon {persentase_diskon}% - Final: Rp {harga_final:,.0f}")

    return DiskonCalculationResponse(
        # Info paket
        nama_paket=paket.nama_paket,
        nama_brand=brand.brand,
        # Harga dasar
        harga_paket=round(harga_paket, 0),
        pajak_persen=pajak_persen,
        pajak_amount=round(pajak_amount, 0),
        subtotal_sebelum_diskon=round(subtotal_sebelum_diskon, 0),
        # Diskon
        persentase_diskon=persentase_diskon,
        diskon_amount=round(diskon_amount, 0),
        # Harga final
        harga_final=round(harga_final, 0),
        # Detail perhitungan
        detail_perhitungan=detail_perhitungan,
    )
