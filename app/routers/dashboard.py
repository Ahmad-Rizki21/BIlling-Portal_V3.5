from fastapi import APIRouter, Depends
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, or_
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio
from pydantic import BaseModel
from collections import defaultdict
import locale

# Impor model dengan nama yang akan kita gunakan secara konsisten
from ..models import Invoice, Pelanggan, HargaLayanan, MikrotikServer, PaketLayanan, Langganan
from sqlalchemy.orm import selectinload
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel

from ..auth import get_current_active_user
from ..database import get_db
from ..services import mikrotik_service

from ..schemas.dashboard import (
    DashboardData,
    StatCard,
    ChartData,
    InvoiceSummary,
    RevenueSummary,
    BrandRevenueItem,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

try:
    locale.setlocale(locale.LC_TIME, "id_ID.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "Indonesian")
    except locale.Error:
        print("Peringatan: Locale Bahasa Indonesia tidak ditemukan.")
        pass

class MikrotikStatus(BaseModel):
    online: int
    offline: int

@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    user_with_role = await db.execute(
        select(UserModel).options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
        .where(UserModel.id == current_user.id)
    )
    user = user_with_role.scalar_one_or_none()

    if not user or not user.role:
        return DashboardData()

    user_permissions = {p.name for p in user.role.permissions}
    dashboard_response = DashboardData()

    # 1. Widget Pendapatan Bulanan
    if "view_widget_pendapatan_bulanan" in user_permissions:
        now = datetime.now()
        revenue_stmt = select(
            HargaLayanan.brand,
            func.sum(Invoice.total_harga).label("total_revenue")
        ).select_from(Invoice).join(
            Pelanggan, Invoice.pelanggan_id == Pelanggan.id, isouter=True
        ).join(
            HargaLayanan, Pelanggan.id_brand == HargaLayanan.id_brand, isouter=True
        ).where(
            Invoice.status_invoice == "Lunas",
            HargaLayanan.brand.is_not(None),
            func.extract("year", Invoice.paid_at) == now.year,
            func.extract("month", Invoice.paid_at) == now.month,
        ).group_by(HargaLayanan.brand)

        revenue_results = (await db.execute(revenue_stmt)).all()
        brand_breakdown = [
            BrandRevenueItem(brand=row.brand, revenue=float(row.total_revenue or 0.0))
            for row in revenue_results
        ]
        total_revenue = sum(item.revenue for item in brand_breakdown)
        next_month_date = now + relativedelta(months=1)
        periode_str = next_month_date.strftime("%B %Y")
        
        dashboard_response.revenue_summary = RevenueSummary(
            total=total_revenue,
            periode=periode_str,
            breakdown=brand_breakdown
        )

    # 2. Widget Statistik
    temp_stat_cards = []
    if "view_widget_statistik_pelanggan" in user_permissions:
        pelanggan_count_stmt = (
            select(HargaLayanan.brand, func.count(Pelanggan.id))
            .join(Pelanggan, HargaLayanan.id_brand == Pelanggan.id_brand, isouter=True)
            .group_by(HargaLayanan.brand)
        )
        pelanggan_counts = (await db.execute(pelanggan_count_stmt)).all()
        pelanggan_by_brand = {brand.lower(): count for brand, count in pelanggan_counts}
        pelanggan_stats = [
            StatCard(title="Jumlah Pelanggan Jakinet", value=pelanggan_by_brand.get("jakinet", 0), description="Total Pelanggan Jakinet"),
            StatCard(title="Jumlah Pelanggan Jelantik", value=pelanggan_by_brand.get("jelantik", 0), description="Total Pelanggan Jelantik"),
            StatCard(title="Pelanggan Jelantik Nagrak", value=pelanggan_by_brand.get("jelantik nagrak", 0), description="Total Pelanggan Rusun Nagrak"),
        ]
        temp_stat_cards.extend(pelanggan_stats)

    if "view_widget_statistik_server" in user_permissions:
        total_servers_stmt = select(func.count(MikrotikServer.id))
        total_servers = (await db.execute(total_servers_stmt)).scalar_one_or_none() or 0
        server_stats = [
            StatCard(title="Total Servers", value=total_servers, description="Total Mikrotik servers"),
            StatCard(title="Online Servers", value="N/A", description="Servers currently online"),
            StatCard(title="Offline Servers", value="N/A", description="Servers currently offline"),
        ]
        temp_stat_cards.extend(server_stats)

    if temp_stat_cards:
        dashboard_response.stat_cards = temp_stat_cards
    # 3. Widget Chart Pelanggan per Lokasi
    if "view_widget_pelanggan_per_lokasi" in user_permissions:
        lokasi_stmt = (
            select(Pelanggan.alamat, func.count(Pelanggan.id))
            .group_by(Pelanggan.alamat)
            .order_by(func.count(Pelanggan.id).desc())
            .limit(5)
        )
        lokasi_data = (await db.execute(lokasi_stmt)).all()
        dashboard_response.lokasi_chart = ChartData(
            labels=[item[0] for item in lokasi_data if item[0] is not None],
            data=[item[1] for item in lokasi_data if item[0] is not None],
        )

    # 4. Widget Chart Pelanggan per Paket
    if "view_widget_pelanggan_per_paket" in user_permissions:
        paket_stmt = (
            select(PaketLayanan.kecepatan, func.count(Langganan.id))
            .join(Langganan, PaketLayanan.id == Langganan.paket_layanan_id, isouter=True)
            .group_by(PaketLayanan.kecepatan)
            .order_by(PaketLayanan.kecepatan)
        )
        paket_data = (await db.execute(paket_stmt)).all()
        dashboard_response.paket_chart = ChartData(
            labels=[f"{item[0]} Mbps" for item in paket_data],
            data=[item[1] for item in paket_data],
        )

    # 5. Widget Chart Tren Pertumbuhan Pelanggan
    if "view_widget_tren_pertumbuhan" in user_permissions:
        growth_stmt = (
            select(
                func.date_format(Pelanggan.tgl_instalasi, "%Y-%m").label("bulan"),
                func.count(Pelanggan.id).label("jumlah"),
            )
            .where(Pelanggan.tgl_instalasi.isnot(None))
            .group_by("bulan")
            .order_by("bulan")
        )
        growth_data = (await db.execute(growth_stmt)).all()
        dashboard_response.growth_chart = ChartData(
            labels=[datetime.strptime(item.bulan, "%Y-%m").strftime("%b %Y") for item in growth_data],
            data=[item.jumlah for item in growth_data],
        )

    # 6. Widget Chart Invoice Bulanan
    if "view_widget_invoice_bulanan" in user_permissions:
        six_months_ago = datetime.now() - timedelta(days=180)
        invoice_stmt = (
            select(
                func.date_format(Invoice.tgl_invoice, "%Y-%m").label("bulan"),
                func.count(Invoice.id).label("total"),
                func.sum(func.if_(Invoice.status_invoice == "Lunas", 1, 0)).label("lunas"),
                func.sum(func.if_(Invoice.status_invoice == "Belum Dibayar", 1, 0)).label("menunggu"),
                func.sum(func.if_(Invoice.status_invoice == "Kadaluarsa", 1, 0)).label("kadaluarsa"),
            )
            .where(Invoice.tgl_invoice >= six_months_ago)
            .group_by("bulan")
            .order_by("bulan")
        )
        invoice_data = (await db.execute(invoice_stmt)).all()
        dashboard_response.invoice_summary_chart = InvoiceSummary(
            labels=[datetime.strptime(item.bulan, "%Y-%m").strftime("%b") for item in invoice_data],
            total=[item.total or 0 for item in invoice_data],
            lunas=[item.lunas or 0 for item in invoice_data],
            menunggu=[item.menunggu or 0 for item in invoice_data],
            kadaluarsa=[item.kadaluarsa or 0 for item in invoice_data],
        )

        # 6. Widget Chart Status Pelanggan
        if "view_widget_status_langganan" in user_permissions: 
        # Pastikan semua baris di dalam blok ini di-indent
            status_stmt = select(
                Langganan.status,
                func.count(Langganan.id).label("jumlah")
            ).group_by(Langganan.status).order_by(Langganan.status)

        status_results = (await db.execute(status_stmt)).all()

        dashboard_response.status_langganan_chart = ChartData(
            labels=[row.status for row in status_results],
            data=[row.jumlah for row in status_results]
        )

    if "view_widget_alamat_aktif" in user_permissions:
    # Pastikan semua baris di bawah ini menjorok ke dalam (di-indent)
        alamat_stmt = (
            select(
                Pelanggan.alamat,
                func.count(Pelanggan.id).label("jumlah")
            )
            .join(Langganan, Pelanggan.id == Langganan.pelanggan_id)
            .where(Langganan.status == "Aktif")
            .group_by(Pelanggan.alamat)
            .order_by(func.count(Pelanggan.id).desc())
            .limit(7)
        )
    
    alamat_results = (await db.execute(alamat_stmt)).all()

    if alamat_results:
        dashboard_response.pelanggan_per_alamat_chart = ChartData(
            labels=[row.alamat for row in alamat_results],
            data=[row.jumlah for row in alamat_results]
        )


    return dashboard_response


# ==========================================================
# --- ENDPOINT STATUS MIKROTIK YANG DIPERBAIKI ---
# ==========================================================
@router.get("/mikrotik-status", response_model=MikrotikStatus)
async def get_mikrotik_status(db: AsyncSession = Depends(get_db)):
    """
    Endpoint terpisah untuk memeriksa status online/offline semua server Mikrotik.
    """
    all_servers = (await db.execute(select(MikrotikServer))).scalars().all()
    total_servers = len(all_servers)

    if total_servers == 0:
        return MikrotikStatus(online=0, offline=0)

    async def check_status(server):
        try:
            loop = asyncio.get_event_loop()
            api, conn = await loop.run_in_executor(
                None, mikrotik_service.get_api_connection, server
            )
            if api and conn:
                conn.disconnect()
                return True
            return False
        except Exception:
            return False

    results = await asyncio.gather(*(check_status(server) for server in all_servers))
    online_servers = sum(1 for res in results if res)
    offline_servers = total_servers - online_servers

    return MikrotikStatus(online=online_servers, offline=offline_servers)

class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int


# Skema untuk respons data badge
class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int


@router.get("/sidebar-badges", response_model=SidebarBadgeResponse)
async def get_sidebar_badges(db: AsyncSession = Depends(get_db)):
    # PERBAIKAN: Menggunakan nama 'Langganan' dan 'Invoice'
    suspended_query = select(func.count(Langganan.id)).where(Langganan.status == "Suspended")
    suspended_result = await db.execute(suspended_query)
    suspended_count = suspended_result.scalar_one_or_none() or 0

    unpaid_query = select(func.count(Invoice.id)).where(Invoice.status_invoice == "Belum Dibayar")
    unpaid_result = await db.execute(unpaid_query)
    unpaid_count = unpaid_result.scalar_one_or_none() or 0

    stopped_query = select(func.count(Langganan.id)).where(Langganan.status == "Berhenti")
    stopped_result = await db.execute(stopped_query)
    stopped_count = stopped_result.scalar_one_or_none() or 0

    return SidebarBadgeResponse(
        suspended_count=suspended_count,
        unpaid_invoice_count=unpaid_count,
        stopped_count=stopped_count,
    )

class GrowthChartData(BaseModel):
    labels: List[str]
    data: List[int]


# ============================================


# =========================================== Chart untuk menampilkan penambahan User =======================================


class GrowthChartData(BaseModel):
    labels: List[str]
    data: List[int]


@router.get("/growth-trend", response_model=GrowthChartData)
async def get_growth_trend_data(db: AsyncSession = Depends(get_db)):
    """
    Menyediakan data untuk grafik tren pertumbuhan pelanggan baru per bulan.
    """
    stmt = (
        select(
            func.date_format(Pelanggan.tgl_instalasi, "%Y-%m").label("bulan"),
            func.count(Pelanggan.id).label("jumlah"),
        )
        .where(Pelanggan.tgl_instalasi.isnot(None))
        .group_by("bulan")
        .order_by("bulan")
    )

    result = await db.execute(stmt)
    growth_data = result.all()

    labels = [
        datetime.strptime(item.bulan, "%Y-%m").strftime("%b %Y") for item in growth_data
    ]
    data = [item.jumlah for item in growth_data]

    return GrowthChartData(labels=labels, data=data)


# =========================================== Chart untuk menampilkan penambahan User =======================================


# --- 1. Definisikan Skema Pydantic Baru untuk Respons ---
# Ini akan mendefinisikan struktur data yang rapi untuk frontend


class BreakdownItem(BaseModel):
    """Mewakili satu item dalam rincian (misal: satu lokasi atau satu brand)."""
    nama: str
    jumlah: int


class PaketDetail(BaseModel):
    """Mewakili rincian lengkap untuk satu jenis paket."""
    total_pelanggan: int
    breakdown_lokasi: List[BreakdownItem]
    breakdown_brand: List[BreakdownItem]

# --- 2. Buat Endpoint API Baru ---


@router.get("/paket-details", response_model=Dict[str, PaketDetail])
async def get_paket_details(db: AsyncSession = Depends(get_db)):
    """
    Endpoint baru untuk memberikan rincian pelanggan per paket,
    dipecah berdasarkan lokasi dan brand.
    """
    stmt = (
        select(
            PaketLayanan.kecepatan,
            Pelanggan.alamat,
            HargaLayanan.brand,
            func.count(Pelanggan.id).label("jumlah"),
        )
        .select_from(PaketLayanan)
        .join(Langganan, PaketLayanan.id == Langganan.paket_layanan_id)
        .join(Pelanggan, Langganan.pelanggan_id == Pelanggan.id)
        .join(HargaLayanan, Pelanggan.id_brand == HargaLayanan.id_brand)
        .group_by(PaketLayanan.kecepatan, Pelanggan.alamat, HargaLayanan.brand)
        .order_by(PaketLayanan.kecepatan, func.count(Pelanggan.id).desc())
    )

    result = await db.execute(stmt)
    raw_data = result.all()

    paket_details = defaultdict(
        lambda: {
            "total_pelanggan": 0,
            "lokasi": defaultdict(int),
            "brand": defaultdict(int),
        }
    )

    for kecepatan, alamat, brand, jumlah in raw_data:
        if not alamat or not brand:
            continue

        paket_key = f"{kecepatan} Mbps"
        details = paket_details[paket_key]

        details["total_pelanggan"] += jumlah
        details["lokasi"][alamat] += jumlah
        details["brand"][brand] += jumlah

    final_response = {}
    for paket_key, details in paket_details.items():
        sorted_lokasi = sorted(
            details["lokasi"].items(), key=lambda item: item[1], reverse=True
        )
        sorted_brand = sorted(
            details["brand"].items(), key=lambda item: item[1], reverse=True
        )

        final_response[paket_key] = PaketDetail(
            total_pelanggan=details["total_pelanggan"],
            breakdown_lokasi=[
                BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_lokasi
            ],
            breakdown_brand=[
                BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_brand
            ],
        )

    return final_response