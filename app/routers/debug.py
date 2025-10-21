"""
Debug router untuk analisis data consistency
Hanya untuk development/debugging, disable di production!
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..auth import get_current_active_user
from ..database import get_db
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel

router = APIRouter(prefix="/debug", tags=["Debug"], include_in_schema=False)


@router.get("/data-consistency", response_model=Dict[str, Any])
async def check_data_consistency(
    db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)
):
    """
    Endpoint untuk debugging data consistency antara langganan dan pelanggan
    """

    # 1. Get all langganan with eager loading
    langganan_query = select(LanggananModel).options(
        joinedload(LanggananModel.pelanggan), joinedload(LanggananModel.paket_layanan)
    )
    langganan_result = await db.execute(langganan_query)
    all_langganan = langganan_result.scalars().unique().all()

    # 2. Get all pelanggan IDs
    pelanggan_query = select(PelangganModel.id)
    pelanggan_result = await db.execute(pelanggan_query)
    all_pelanggan_ids = set(pelanggan_result.scalars().all())

    # 3. Find inconsistent data
    inconsistent_langganan = []
    for langganan in all_langganan:
        if langganan.pelanggan_id not in all_pelanggan_ids:
            inconsistent_langganan.append(
                {
                    "langganan_id": langganan.id,
                    "pelanggan_id": langganan.pelanggan_id,
                    "status": langganan.status,
                    "paket_layanan_id": langganan.paket_layanan_id,
                    "paket_nama": langganan.paket_layanan.nama_paket if langganan.paket_layanan else None,
                    "metode_pembayaran": langganan.metode_pembayaran,
                    "tgl_jatuh_tempo": str(langganan.tgl_jatuh_tempo) if langganan.tgl_jatuh_tempo else None,
                }
            )

    # 4. Check specific cases
    specific_checks = {}

    # Check langganan ID 244
    langganan_244 = [l for l in all_langganan if l.id == 244]
    if langganan_244:
        langg = langganan_244[0]
        specific_checks["langganan_244"] = {
            "exists": True,
            "pelanggan_id": langg.pelanggan_id,
            "pelanggan_exists": langg.pelanggan_id in all_pelanggan_ids,
            "pelanggan_nama": langg.pelanggan.nama if langg.pelanggan else None,
            "status": langg.status,
        }
    else:
        specific_checks["langganan_244"] = {"exists": False}

    # Check pelanggan ID 258
    pelanggan_258 = 258 in all_pelanggan_ids
    specific_checks["pelanggan_258"] = {"exists": pelanggan_258}

    # Find all langganan with pelanggan_id 258
    langganan_with_pelanggan_258 = [
        {"id": l.id, "status": l.status, "paket_nama": l.paket_layanan.nama_paket if l.paket_layanan else None}
        for l in all_langganan
        if l.pelanggan_id == 258
    ]
    specific_checks["langganan_with_pelanggan_258"] = langganan_with_pelanggan_258

    return {
        "total_langganan": len(all_langganan),
        "total_pelanggan": len(all_pelanggan_ids),
        "inconsistent_langganan_count": len(inconsistent_langganan),
        "inconsistent_langganan": inconsistent_langganan[:10],  # Limit to 10 for response size
        "specific_checks": specific_checks,
        "has_inconsistencies": len(inconsistent_langganan) > 0,
    }


@router.get("/orphaned-invoices", response_model=Dict[str, Any])
async def check_orphaned_invoices(
    db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)
):
    """
    Cek invoice yang mereferensikan pelanggan yang tidak ada
    """
    from ..models.invoice import Invoice as InvoiceModel

    # Get all invoices with pelanggan data
    invoice_query = select(InvoiceModel).options(joinedload(InvoiceModel.pelanggan))
    invoice_result = await db.execute(invoice_query)
    all_invoices = invoice_result.scalars().unique().all()

    orphaned_invoices = []
    for invoice in all_invoices:
        if not invoice.pelanggan:
            orphaned_invoices.append(
                {
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "pelanggan_id": invoice.pelanggan_id,
                    "status_invoice": invoice.status_invoice,
                    "total_harga": str(invoice.total_harga),
                    "tgl_invoice": str(invoice.tgl_invoice),
                }
            )

    return {
        "total_invoices": len(all_invoices),
        "orphaned_invoices_count": len(orphaned_invoices),
        "orphaned_invoices": orphaned_invoices[:10],  # Limit to 10
    }
