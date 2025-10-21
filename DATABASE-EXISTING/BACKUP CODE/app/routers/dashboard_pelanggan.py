# app/routers/dashboard_pelanggan.py

import asyncio
import logging
import traceback
from datetime import date, datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import and_, case, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel


# --- Skema Pydantic untuk respons Chart ---
class ChartData(BaseModel):
    labels: List[str]
    data: List[int | float]

# --- Skema Pydantic untuk respons Statistik Utama ---
class MainStats(BaseModel):
    pelanggan_aktif: int
    pelanggan_baru_bulan_ini: int
    pelanggan_berhenti_bulan_ini: int
    pelanggan_jakinet_aktif: int
    pendapatan_jakinet_bulan_ini: float

# --- Skema Pydantic untuk respons Dashboard Pelanggan yang Terpadu ---
class DashboardPelangganData(BaseModel):
    main_stats: MainStats
    growth_chart: ChartData
    revenue_chart: ChartData


router = APIRouter(
    prefix="/dashboard-pelanggan",
    tags=["Dashboard Pelanggan"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

# --- Helper Functions (Logika dari endpoint lama yang di-refactor) ---

async def _get_main_statistics(db: AsyncSession) -> MainStats:
    """
    Menyediakan data utama untuk kartu statistik di dashboard pelanggan.
    """
    today = date.today()
    first_day_of_month = today.replace(day=1)

    # --- OPTIMISASI: Gabungkan beberapa query menjadi satu ---
    # Query untuk statistik pelanggan Jakinet
    jakinet_stats_stmt = (
        select(
            func.count(LanggananModel.id).label("total_langganan"),
            func.sum(
                case((LanggananModel.status == "Aktif", 1), else_=0)
            ).label("pelanggan_aktif"),
            func.sum(
                case(
                    (LanggananModel.tgl_mulai_langganan >= first_day_of_month, 1),
                    else_=0,
                )
            ).label("pelanggan_baru_bulan_ini"),
            func.sum(  # PERBAIKAN: Memperbaiki struktur tuple untuk case statement
                case(
                    (
                        (LanggananModel.status == "Berhenti")
                        & (LanggananModel.tgl_berhenti >= first_day_of_month),
                        1,
                    ),  # Pastikan ini adalah satu tuple (kondisi, hasil)
                    else_=0,
                )
            ).label("pelanggan_berhenti_bulan_ini"),
        )
        .join(LanggananModel.pelanggan)
        .where(PelangganModel.id_brand == "ajn-01")
    )
    jakinet_stats_result = (await db.execute(jakinet_stats_stmt)).first()

    # Query untuk pendapatan Jakinet (tetap terpisah karena dari tabel Invoice)
    q_pendapatan = (
        select(func.sum(InvoiceModel.paid_amount))
        .join(InvoiceModel.pelanggan)
        .where(
            InvoiceModel.status_invoice == "Lunas",
            PelangganModel.id_brand == "ajn-01",
            InvoiceModel.paid_at >= first_day_of_month,
        )
    )
    pendapatan_jakinet_bulan_ini = (
        await db.execute(q_pendapatan)
    ).scalar_one_or_none() or 0.0

    # PERBAIKAN: Handle kasus jika tidak ada pelanggan Jakinet sama sekali
    if not jakinet_stats_result:
        return MainStats(
            pelanggan_aktif=0,
            pelanggan_baru_bulan_ini=0,
            pelanggan_berhenti_bulan_ini=0,
            pelanggan_jakinet_aktif=0,
            pendapatan_jakinet_bulan_ini=0.0,
        )

    return MainStats(
        pelanggan_aktif=jakinet_stats_result.pelanggan_aktif or 0,
        pelanggan_baru_bulan_ini=jakinet_stats_result.pelanggan_baru_bulan_ini or 0,
        pelanggan_berhenti_bulan_ini=jakinet_stats_result.pelanggan_berhenti_bulan_ini or 0,
        pelanggan_jakinet_aktif=jakinet_stats_result.pelanggan_aktif or 0,
        pendapatan_jakinet_bulan_ini=float(pendapatan_jakinet_bulan_ini),
    )


async def _get_growth_trend(db: AsyncSession) -> ChartData:
    """
    Menyediakan data tren pertumbuhan pelanggan Jakinet selama 6 bulan terakhir.
    Dioptimalkan untuk menghindari N+1 query.
    """
    today = date.today()
    six_months_ago = today - relativedelta(months=5)
    first_day_of_period = six_months_ago.replace(day=1)

    # 1. Ambil semua data langganan baru Jakinet dalam periode 6 bulan dalam satu query
    stmt = (
        select(
            func.date_format(LanggananModel.tgl_mulai_langganan, "%Y-%m").label(
                "bulan"
            ),
            func.count(LanggananModel.id).label("jumlah_baru"),
        )
        .join(LanggananModel.pelanggan)
        .where(
            PelangganModel.id_brand == "ajn-01",
            LanggananModel.tgl_mulai_langganan >= first_day_of_period,
        )
        .group_by("bulan")
        .order_by("bulan")
    )
    result = (await db.execute(stmt)).all()
    monthly_new_subs = {row.bulan: row.jumlah_baru for row in result}

    # 2. Hitung total pelanggan Jakinet sebelum periode 6 bulan ini sebagai basis
    base_count_stmt = (
        select(func.count(LanggananModel.id))
        .join(LanggananModel.pelanggan)
        .where(
            PelangganModel.id_brand == "ajn-01",
            LanggananModel.tgl_mulai_langganan < first_day_of_period,
        )
    )
    cumulative_total = (await db.execute(base_count_stmt)).scalar_one_or_none() or 0

    # 3. Proses data di Python untuk membuat tren kumulatif
    labels = []
    jakinet_growth_data = []
    for i in range(5, -1, -1):
        target_date = today - relativedelta(months=i)
        month_key = target_date.strftime("%Y-%m")
        month_label = target_date.strftime("%b")
        labels.append(month_label)

        # Tambahkan pelanggan baru dari bulan ini ke total kumulatif
        cumulative_total += monthly_new_subs.get(month_key, 0)
        jakinet_growth_data.append(cumulative_total)

    return ChartData(labels=labels, data=jakinet_growth_data)


async def _get_jakinet_revenue_trend(
    timespan: str = "6m", db: AsyncSession = Depends(get_db)
):
    """
    Menyediakan data tren pendapatan JakiNet berdasarkan rentang waktu.
    Dioptimalkan untuk menghindari N+1 query.
    """
    months_map = {"3m": 3, "6m": 6, "1y": 12}
    num_months = months_map.get(timespan, 6)

    today = datetime.now()
    start_period = today - relativedelta(months=num_months - 1)
    first_day_of_period = start_period.replace(day=1, hour=0, minute=0, second=0)

    # 1. Ambil semua data pendapatan Jakinet dalam periode yang diminta dalam satu query
    stmt = (
        select(
            func.date_format(InvoiceModel.paid_at, "%Y-%m").label("bulan"),
            func.sum(InvoiceModel.paid_amount).label("total_revenue"),
        )
        .join(InvoiceModel.pelanggan)
        .where(
            InvoiceModel.status_invoice == "Lunas",
            PelangganModel.id_brand == "ajn-01",
            InvoiceModel.paid_at >= first_day_of_period,
        )
        .group_by("bulan")
        .order_by("bulan")
    )
    result = (await db.execute(stmt)).all()
    monthly_revenue_map = {row.bulan: float(row.total_revenue or 0) for row in result}

    # 2. Proses data di Python untuk memastikan semua bulan ada (termasuk yang 0)
    labels = []
    revenue_data = []
    for i in range(num_months - 1, -1, -1):
        target_date = today - relativedelta(months=i)
        month_key = target_date.strftime("%Y-%m")
        month_label = target_date.strftime("%b %y")

        labels.append(month_label)
        revenue_data.append(monthly_revenue_map.get(month_key, 0.0))

    return ChartData(labels=labels, data=revenue_data)


# --- ENDPOINT UTAMA YANG SUDAH DIOPTIMALKAN ---

@router.get("/", response_model=DashboardPelangganData)
async def get_dashboard_pelanggan_data(
    timespan: str = "6m", db: AsyncSession = Depends(get_db)
):
    """
    Mengambil semua data untuk Dashboard Pelanggan dalam satu panggilan API.
    Semua query ke database dijalankan secara paralel untuk performa maksimal.
    """
    # Kumpulkan semua tugas async
    stats_task = asyncio.create_task(_get_main_statistics(db))
    growth_task = asyncio.create_task(_get_growth_trend(db))
    revenue_task = asyncio.create_task(_get_jakinet_revenue_trend(timespan, db))

    # Jalankan semua tugas secara bersamaan
    results = await asyncio.gather(stats_task, growth_task, revenue_task, return_exceptions=True)

    # Cek jika ada error saat menjalankan tugas
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Log traceback lengkap untuk debugging di sisi server
            tb_str = traceback.format_exception(type(result), result, result.__traceback__)
            logger.error(f"Error in dashboard_pelanggan task {i+1}: {''.join(tb_str)}")
            
            # Kirim respons error yang jelas ke client
            raise HTTPException(
                status_code=500, 
                detail=f"Gagal mengambil data untuk bagian ke-{i+1} dari dashboard: {str(result)}"
            )

    # Susun respons
    response = DashboardPelangganData(main_stats=results[0], growth_chart=results[1], revenue_chart=results[2])
    return response
