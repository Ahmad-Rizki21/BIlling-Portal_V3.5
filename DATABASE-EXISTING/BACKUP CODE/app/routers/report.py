from datetime import date, datetime, time
from typing import List, Optional

import pytz
from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import aliased, selectinload

from ..auth import get_current_active_user  # Sesuaikan path jika berbeda
from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananMode
from ..models.invoice import Invoice as InvoiceModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.user import User as UserModel

# Impor model, skema, dan dependensi yang relevan
from ..schemas.report import InvoiceReportItem, RevenueReportResponse

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

    # --- KONDISI FILTER UMUM ---
    filter_conditions = [
        InvoiceModel.status_invoice == "Lunas",
        InvoiceModel.paid_at.between(start_datetime, end_datetime),
    ]
    if alamat:
        filter_conditions.append(PelangganModel.alamat == alamat)
    if id_brand:
        filter_conditions.append(PelangganModel.id_brand == id_brand)

    # --- QUERY UNTUK SUMMARY (TOTAL PENDAPATAN & JUMLAH INVOICE) ---
    summary_query = (
        select(
            func.coalesce(func.sum(InvoiceModel.total_harga), 0.0),
            func.count(InvoiceModel.id)
        )
        .join(InvoiceModel.pelanggan)
        .where(and_(*filter_conditions))
    )
    total_pendapatan, total_invoices = (await db.execute(summary_query)).one()

    # HAPUS SEMUA LOGIKA UNTUK MENGAMBIL RINCIAN DARI ENDPOINT INI
    # KITA AKAN BUAT ENDPOINT BARU UNTUK ITU

    return RevenueReportResponse(
        total_pendapatan=float(total_pendapatan),
        total_invoices=total_invoices,
        rincian_invoice=[],  # Selalu kembalikan list kosong
    )


@router.get("/revenue/details", response_model=List[InvoiceReportItem])
async def get_revenue_report_details(
    start_date: date,
    end_date: date,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    skip: int = 0,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Endpoint baru yang HANYA mengambil rincian invoice dengan paginasi.
    """
    start_datetime = datetime.combine(start_date, time.min)
    end_datetime = datetime.combine(end_date, time.max)

    # --- KONDISI FILTER UMUM (SAMA SEPERTI DI ATAS) ---
    filter_conditions = [
        InvoiceModel.status_invoice == "Lunas",
        InvoiceModel.paid_at.between(start_datetime, end_datetime),
    ]
    if alamat:
        filter_conditions.append(PelangganModel.alamat == alamat)
    if id_brand:
        filter_conditions.append(PelangganModel.id_brand == id_brand)

    # --- QUERY UNTUK RINCIAN INVOICE (DENGAN PAGINASI) ---
    invoices_query = (
        select(InvoiceModel)
        .join(InvoiceModel.pelanggan)
        .options(
            selectinload(InvoiceModel.pelanggan).selectinload(
                PelangganModel.harga_layanan
            )
        )
        .where(and_(*filter_conditions))
        .order_by(InvoiceModel.paid_at.desc())
        .offset(skip)
    )

    if limit is not None:
        invoices_query = invoices_query.limit(limit)

    invoices_result = await db.execute(invoices_query)
    invoices = invoices_result.scalars().unique().all()

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

    # Kembalikan hanya list rinciannya
    return rincian_invoice_list
