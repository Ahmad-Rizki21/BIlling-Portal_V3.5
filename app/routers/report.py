from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from sqlalchemy.orm import selectinload, aliased
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
            func.count(InvoiceModel.id),
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
    # Query untuk mendapatkan invoice dan informasi pelanggan sekaligus
    invoices_query = (
        select(
            InvoiceModel.id,
            InvoiceModel.invoice_number,
            InvoiceModel.total_harga,
            InvoiceModel.paid_at,
            InvoiceModel.metode_pembayaran,
            InvoiceModel.tgl_jatuh_tempo,
            InvoiceModel.pelanggan_id,
            PelangganModel.nama,
            PelangganModel.alamat,
            PelangganModel.id_brand,
        )
        .join(InvoiceModel.pelanggan)
        .where(and_(*filter_conditions))
        .order_by(InvoiceModel.paid_at.desc())
        .offset(skip)
    )

    if limit is not None:
        invoices_query = invoices_query.limit(limit)

    invoices_result = await db.execute(invoices_query)
    invoice_pelanggan_data = invoices_result.fetchall()

    rincian_invoice_list = []
    wib_timezone = pytz.timezone("Asia/Jakarta")

    # Ambil semua id_brand unik untuk query harga_layanan
    id_brands = [data.id_brand for data in invoice_pelanggan_data if data.id_brand]

    # Query harga_layanan terkait
    brand_harga_layanan = {}
    if id_brands:
        harga_layanan_query = select(HargaLayananMode).where(HargaLayananMode.id_brand.in_(id_brands))
        harga_layanan_result = await db.execute(harga_layanan_query)
        for harga_layanan in harga_layanan_result.scalars().all():
            brand_harga_layanan[harga_layanan.id_brand] = harga_layanan

    for data in invoice_pelanggan_data:
        # Tentukan tipe invoice berdasarkan tanggal jatuh tempo
        invoice_type = "Otomatis"
        if data.tgl_jatuh_tempo and data.tgl_jatuh_tempo.day > 1:
            invoice_type = "Prorate"

        # Tentukan metode pembayaran final
        metode_pembayaran_final = data.metode_pembayaran
        if not metode_pembayaran_final:
            # Jika kosong (via Xendit), gabungkan dengan tipe invoice
            metode_pembayaran_final = f"Xendit - {invoice_type}"

        paid_at_wib = None
        if data.paid_at:
            # Pastikan paid_at adalah timezone-aware (UTC)
            utc_time = data.paid_at.replace(tzinfo=pytz.utc)
            # Konversi ke WIB
            paid_at_wib = utc_time.astimezone(wib_timezone)

        # Get harga_layanan berdasarkan id_brand
        harga_layanan = brand_harga_layanan.get(data.id_brand)

        # Buat item laporan
        report_item = InvoiceReportItem(
            invoice_number=data.invoice_number,
            pelanggan_nama=data.nama if data.nama else "N/A",
            paid_at=paid_at_wib,
            total_harga=data.total_harga,
            metode_pembayaran=metode_pembayaran_final,  # Gunakan nilai yang sudah diproses
            alamat=data.alamat if data.alamat else "N/A",
            id_brand=harga_layanan.brand if harga_layanan else "N/A",
        )
        rincian_invoice_list.append(report_item)

    # Kembalikan hanya list rinciannya
    return rincian_invoice_list
