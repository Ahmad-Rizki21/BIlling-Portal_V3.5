# app/routers/dashboard_pelanggan.py

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
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

router = APIRouter(
    prefix="/dashboard-pelanggan",
    tags=["Dashboard Pelanggan"],
    responses={404: {"description": "Not found"}},
)

@router.get("/statistik-utama")
async def get_main_statistics(db: AsyncSession = Depends(get_db)):
    """
    Menyediakan data utama untuk kartu statistik di dashboard pelanggan.
    """
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    # Inisialisasi variabel dengan nilai default
    pelanggan_aktif = 0
    pelanggan_baru_bulan_ini = 0
    pelanggan_berhenti_bulan_ini = 0
    pelanggan_jakinet_aktif = 0
    pendapatan_jakinet_bulan_ini = 0

    # 1. Hitung Pelanggan Aktif
    q_aktif = select(func.count(LanggananModel.id)).where(LanggananModel.status == 'Aktif')
    res_aktif = await db.execute(q_aktif)
    pelanggan_aktif = res_aktif.scalar_one_or_none() or 0

    # 2. Hitung Pelanggan Baru Bulan Ini
    q_baru = select(func.count(LanggananModel.id)).where(
        LanggananModel.tgl_mulai_langganan >= first_day_of_month
    )
    res_baru = await db.execute(q_baru)
    pelanggan_baru_bulan_ini = res_baru.scalar_one_or_none() or 0

    # 3. Hitung Pelanggan Berhenti Bulan Ini
    q_berhenti = select(func.count(LanggananModel.id)).where(
        LanggananModel.status == 'Berhenti',
        LanggananModel.tgl_berhenti >= first_day_of_month
    )
    res_berhenti = await db.execute(q_berhenti)
    pelanggan_berhenti_bulan_ini = res_berhenti.scalar_one_or_none() or 0
    
    # 4. Hitung Pelanggan Aktif Khusus Brand Jakinet
    q_jakinet = (
        select(func.count(LanggananModel.id))
        .join(LanggananModel.pelanggan)
        .where(
            LanggananModel.status == 'Aktif',
            PelangganModel.id_brand == 'ajn-01' 
        )
    )
    res_jakinet = await db.execute(q_jakinet)
    pelanggan_jakinet_aktif = res_jakinet.scalar_one_or_none() or 0

    # 5. Hitung Pendapatan Khusus Jakinet
    q_pendapatan = (
        select(func.sum(InvoiceModel.paid_amount))
        .join(InvoiceModel.pelanggan)
        .where(
            InvoiceModel.status_invoice == 'Lunas',
            PelangganModel.id_brand == 'ajn-01', # Filter khusus brand Jakinet
            InvoiceModel.paid_at >= first_day_of_month # Filter pembayaran bulan ini
        )
    )
    res_pendapatan = await db.execute(q_pendapatan)
    pendapatan_jakinet_bulan_ini = float(res_pendapatan.scalar_one_or_none() or 0)

    return {
        "pelanggan_aktif": pelanggan_aktif,
        "pelanggan_baru_bulan_ini": pelanggan_baru_bulan_ini,
        "pelanggan_berhenti_bulan_ini": pelanggan_berhenti_bulan_ini,
        "pelanggan_jakinet_aktif": pelanggan_jakinet_aktif,
        "pendapatan_jakinet_bulan_ini": pendapatan_jakinet_bulan_ini, 
    }

# --- ENDPOINT BARU UNTUK CHART ---

@router.get("/tren-pertumbuhan", response_model=ChartData)
async def get_growth_trend(db: AsyncSession = Depends(get_db)):
    """
    Menyediakan data tren pertumbuhan pelanggan baru dan Jakinet selama 6 bulan terakhir.
    """
    labels = []
    total_pelanggan_data = []
    jakinet_data = []
    today = date.today()

    for i in range(5, -1, -1):
        target_date = today - relativedelta(months=i)
        month_label = target_date.strftime("%b")
        labels.append(month_label)

        # Hitung total pelanggan aktif pada akhir bulan tersebut
        q_total = select(func.count(LanggananModel.id)).where(
            LanggananModel.status == 'Aktif',
            func.date(LanggananModel.tgl_mulai_langganan) <= target_date.replace(day=28) # Perkiraan akhir bulan
        )
        total_pelanggan_data.append((await db.execute(q_total)).scalar_one_or_none() or 0)

        # Hitung pelanggan Jakinet aktif pada akhir bulan tersebut
        q_jakinet = (
            select(func.count(LanggananModel.id))
            .join(LanggananModel.pelanggan)
            .where(
                LanggananModel.status == 'Aktif',
                PelangganModel.id_brand == 'ajn-01',
                func.date(LanggananModel.tgl_mulai_langganan) <= target_date.replace(day=28)
            )
        )
        jakinet_data.append((await db.execute(q_jakinet)).scalar_one_or_none() or 0)

    # Mengembalikan data dalam format yang bisa digunakan oleh chart di frontend
    # Di frontend, Anda akan membuat 2 dataset dari data ini.
    return {
        "labels": labels,
        "datasets": {
            "total_pelanggan": total_pelanggan_data,
            "jakinet": jakinet_data
        }
    }


@router.get("/tren-pendapatan-jakinet", response_model=ChartData)
async def get_jakinet_revenue_trend(timespan: str = "6m", db: AsyncSession = Depends(get_db)):
    """
    Menyediakan data tren pendapatan JakiNet berdasarkan rentang waktu (3m, 6m, 1y).
    """
    months_map = {'3m': 3, '6m': 6, '1y': 12}
    num_months = months_map.get(timespan, 6)
    
    today = datetime.now()
    labels = []
    revenue_data = []

    for i in range(num_months - 1, -1, -1):
        target_date = today - relativedelta(months=i)
        first_day = target_date.replace(day=1)
        last_day = (first_day + relativedelta(months=1)) - timedelta(days=1)
        
        labels.append(target_date.strftime("%b %y"))

        q_pendapatan = (
            select(func.sum(InvoiceModel.paid_amount))
            .join(InvoiceModel.pelanggan)
            .where(
                InvoiceModel.status_invoice == 'Lunas',
                PelangganModel.id_brand == 'ajn-01',
                InvoiceModel.paid_at >= first_day,
                InvoiceModel.paid_at <= last_day
            )
        )
        result = await db.execute(q_pendapatan)
        monthly_revenue = float(result.scalar_one_or_none() or 0)
        revenue_data.append(monthly_revenue)
        
    return ChartData(labels=labels, data=revenue_data)