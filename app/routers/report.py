from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
import pytz
from datetime import date, datetime, time
from typing import List, Optional

# Impor model, skema, dan dependensi yang relevan
from ..schemas.report import RevenueReportResponse, InvoiceReportItem
from ..models.invoice import Invoice as InvoiceModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel
from ..database import get_db
from ..auth import get_current_active_user  # Sesuaikan path jika berbeda
from ..models.harga_layanan import HargaLayanan as HargaLayananMode

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
    responses={404: {"description": "Not found"}},
)


@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    start_date: date,
    end_date: date,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)

    # Query 1: Menghitung total pendapatan
    total_revenue_query = (
        select(func.sum(InvoiceModel.total_harga))
        .join(InvoiceModel.pelanggan)  # 2. Join tabel Pelanggan untuk filter
        .where(
            InvoiceModel.status_invoice == "Lunas",
            InvoiceModel.paid_at.between(start_datetime, end_datetime),
        )
    )
    if alamat:  # 3. Terapkan filter jika 'alamat' diberikan
        total_revenue_query = total_revenue_query.where(PelangganModel.alamat == alamat)

    if id_brand:
        total_revenue_query = total_revenue_query.where(PelangganModel.id_brand == id_brand)

    total_revenue_result = await db.execute(total_revenue_query)
    total_pendapatan = total_revenue_result.scalar_one_or_none() or 0.0

    # Query untuk rincian invoice (tidak ada perubahan)
    invoices_query = (
        select(InvoiceModel)
        .join(InvoiceModel.pelanggan)  # Join sudah ada, bagus!
        .options(
            selectinload(InvoiceModel.pelanggan).selectinload(
                PelangganModel.harga_layanan
            )
        )
        .where(
            InvoiceModel.status_invoice == "Lunas",
            InvoiceModel.paid_at.between(start_datetime, end_datetime),
        )
        .order_by(InvoiceModel.paid_at.desc())
    )
    if alamat:  # 3. Terapkan filter jika 'alamat' diberikan
        invoices_query = invoices_query.where(PelangganModel.alamat == alamat)
    
    if id_brand:
        invoices_query = invoices_query.where(PelangganModel.id_brand == id_brand)

    invoices_result = await db.execute(invoices_query)
    invoices = invoices_result.scalars().unique().all()

    # --- PERBARUAN LOGIKA UTAMA ADA DI SINI ---
    rincian_invoice_list = []
    wib_timezone = pytz.timezone("Asia/Jakarta")
    for inv in invoices:
        # Tentukan tipe invoice berdasarkan tanggal jatuh tempo
        invoice_type = "Otomatis"
        if inv.tgl_jatuh_tempo and inv.tgl_jatuh_tempo.day > 1:
            invoice_type = "Prorate"

        # Tentukan metode pembayaran final
        metode_pembayaran_final = inv.metode_pembayaran
        if not metode_pembayaran_final:
            # Jika kosong (via Xendit), gabungkan dengan tipe invoice
            metode_pembayaran_final = f"Xendit - {invoice_type}"

        paid_at_wib = None
        if inv.paid_at:
            # Pastikan paid_at adalah timezone-aware (UTC)
            utc_time = inv.paid_at.replace(tzinfo=pytz.utc)
            # Konversi ke WIB
            paid_at_wib = utc_time.astimezone(wib_timezone)

        # Buat item laporan
        report_item = InvoiceReportItem(
            invoice_number=inv.invoice_number,
            pelanggan_nama=inv.pelanggan.nama if inv.pelanggan else "N/A",
            paid_at=paid_at_wib,
            total_harga=inv.total_harga,
            metode_pembayaran=metode_pembayaran_final,  # Gunakan nilai yang sudah diproses
            alamat=inv.pelanggan.alamat if inv.pelanggan else "N/A",
            id_brand=(
                inv.pelanggan.harga_layanan.brand
                if inv.pelanggan and inv.pelanggan.harga_layanan
                else "N/A"
            ),
        )
        rincian_invoice_list.append(report_item)

    return RevenueReportResponse(
        total_pendapatan=total_pendapatan, rincian_invoice=rincian_invoice_list
    )
