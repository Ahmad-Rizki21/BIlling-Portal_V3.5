# app/routers/dashboard_pelanggan.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, case, and_
import asyncio
import logging
import traceback
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List

from ..database import get_db
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.invoice import Invoice as InvoiceModel
from pydantic import BaseModel


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


async def _get_main_statistics() -> MainStats:
    """
    Menyediakan data utama untuk kartu statistik di dashboard pelanggan.
    Setiap pemanggilan fungsi ini akan menggunakan sesi database-nya sendiri.
    """
    async for db in get_db():
        try:
            today = date.today()
            first_day_of_month = today.replace(day=1)

            # Query untuk statistik pelanggan Jakinet
            jakinet_stats_stmt = (
                select(
                    func.count(LanggananModel.id).label("total_langganan"),
                    func.sum(case((LanggananModel.status == "Aktif", 1), else_=0)).label("pelanggan_aktif"),
                    func.sum(
                        case(
                            (LanggananModel.tgl_mulai_langganan >= first_day_of_month, 1),
                            else_=0,
                        )
                    ).label("pelanggan_baru_bulan_ini"),
                    func.sum(
                        case(
                            (
                                (LanggananModel.status == "Berhenti") & (LanggananModel.tgl_berhenti >= first_day_of_month),
                                1,
                            ),
                            else_=0,
                        )
                    ).label("pelanggan_berhenti_bulan_ini"),
                )
                .join(LanggananModel.pelanggan)
                .where(PelangganModel.id_brand == "ajn-01")
            )
            jakinet_stats_result = (await db.execute(jakinet_stats_stmt)).first()

            # Query untuk pendapatan Jakinet
            q_pendapatan = (
                select(func.sum(InvoiceModel.paid_amount))
                .join(InvoiceModel.pelanggan)
                .where(
                    InvoiceModel.status_invoice == "Lunas",
                    PelangganModel.id_brand == "ajn-01",
                    InvoiceModel.paid_at >= first_day_of_month,
                )
            )
            pendapatan_jakinet_bulan_ini = (await db.execute(q_pendapatan)).scalar_one_or_none() or 0.0

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
        except Exception as e:
            logger.error(f"Error in _get_main_statistics: {str(e)}")
            return MainStats(
                pelanggan_aktif=0,
                pelanggan_baru_bulan_ini=0,
                pelanggan_berhenti_bulan_ini=0,
                pelanggan_jakinet_aktif=0,
                pendapatan_jakinet_bulan_ini=0.0,
            )

    # Return default value if no database session was obtained
    return MainStats(
        pelanggan_aktif=0,
        pelanggan_baru_bulan_ini=0,
        pelanggan_berhenti_bulan_ini=0,
        pelanggan_jakinet_aktif=0,
        pendapatan_jakinet_bulan_ini=0.0,
    )


async def _get_growth_trend() -> ChartData:
    """
    Menyediakan data tren pertumbuhan pelanggan Jakinet selama 6 bulan terakhir.
    Setiap pemanggilan fungsi ini akan menggunakan sesi database-nya sendiri.
    """
    async for db in get_db():
        try:
            today = date.today()
            six_months_ago = today - relativedelta(months=5)
            first_day_of_period = six_months_ago.replace(day=1)

            stmt = (
                select(
                    func.date_format(LanggananModel.tgl_mulai_langganan, "%Y-%m").label("bulan"),
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

            base_count_stmt = (
                select(func.count(LanggananModel.id))
                .join(LanggananModel.pelanggan)
                .where(
                    PelangganModel.id_brand == "ajn-01",
                    LanggananModel.tgl_mulai_langganan < first_day_of_period,
                )
            )
            cumulative_total = (await db.execute(base_count_stmt)).scalar_one_or_none() or 0

            labels = []
            jakinet_growth_data = []
            for i in range(5, -1, -1):
                target_date = today - relativedelta(months=i)
                month_key = target_date.strftime("%Y-%m")
                month_label = target_date.strftime("%b")
                labels.append(month_label)
                cumulative_total += monthly_new_subs.get(month_key, 0)
                jakinet_growth_data.append(cumulative_total)

            return ChartData(labels=labels, data=jakinet_growth_data)
        except Exception as e:
            logger.error(f"Error in _get_growth_trend: {str(e)}")
            return ChartData(labels=["Error"], data=[0])

    # Return default value if no database session was obtained
    return ChartData(labels=["Error"], data=[0])


async def _get_jakinet_revenue_trend(timespan: str = "6m") -> ChartData:
    """
    Menyediakan data tren pendapatan JakiNet berdasarkan rentang waktu.
    Setiap pemanggilan fungsi ini akan menggunakan sesi database-nya sendiri.
    """
    async for db in get_db():
        try:
            months_map = {"3m": 3, "6m": 6, "1y": 12}
            num_months = months_map.get(timespan, 6)

            today = datetime.now()
            start_period = today - relativedelta(months=num_months - 1)
            first_day_of_period = start_period.replace(day=1, hour=0, minute=0, second=0)

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

            labels = []
            revenue_data = []
            for i in range(num_months - 1, -1, -1):
                target_date = today - relativedelta(months=i)
                month_key = target_date.strftime("%Y-%m")
                month_label = target_date.strftime("%b %y")
                labels.append(month_label)
                revenue_data.append(monthly_revenue_map.get(month_key, 0.0))

            return ChartData(labels=labels, data=revenue_data)
        except Exception as e:
            logger.error(f"Error in _get_jakinet_revenue_trend: {str(e)}")
            return ChartData(labels=["Error"], data=[0.0])

    # Return default value if no database session was obtained
    return ChartData(labels=["Error"], data=[0.0])


# --- ENDPOINT UTAMA YANG SUDAH DIOPTIMALKAN ---


@router.get("/", response_model=DashboardPelangganData)
async def get_dashboard_pelanggan_data(timespan: str = "6m"):
    """
    Mengambil semua data untuk Dashboard Pelanggan dalam satu panggilan API.
    Setiap tugas query ke database dijalankan secara paralel dengan sesi DB-nya sendiri.
    """
    # Kumpulkan semua tugas async. Setiap tugas mengelola sesi DB-nya sendiri.
    stats_task = asyncio.create_task(_get_main_statistics())
    growth_task = asyncio.create_task(_get_growth_trend())
    revenue_task = asyncio.create_task(_get_jakinet_revenue_trend(timespan=timespan))

    # Jalankan semua tugas secara bersamaan
    results = await asyncio.gather(stats_task, growth_task, revenue_task, return_exceptions=True)

    # Cek jika ada error saat menjalankan tugas
    main_stats = (
        results[0]
        if not isinstance(results[0], Exception)
        else MainStats(
            pelanggan_aktif=0,
            pelanggan_baru_bulan_ini=0,
            pelanggan_berhenti_bulan_ini=0,
            pelanggan_jakinet_aktif=0,
            pendapatan_jakinet_bulan_ini=0.0,
        )
    )
    growth_chart = results[1] if not isinstance(results[1], Exception) else ChartData(labels=["Error"], data=[0])
    revenue_chart = results[2] if not isinstance(results[2], Exception) else ChartData(labels=["Error"], data=[0.0])

    # Log errors jika ada
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            tb_str = traceback.format_exception(type(result), result, result.__traceback__)
            logger.error(f"Error in dashboard_pelanggan task {i+1}: {''.join(tb_str)}")

    # Susun respons
    response = DashboardPelangganData(
        main_stats=main_stats,  # type: ignore
        growth_chart=growth_chart,  # type: ignore
        revenue_chart=revenue_chart,  # type: ignore
    )
    return response
