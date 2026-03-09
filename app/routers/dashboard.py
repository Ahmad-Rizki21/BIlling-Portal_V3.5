from fastapi import APIRouter, Depends, HTTPException, Response, Query
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, or_, and_, not_
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio
import time
from pydantic import BaseModel
from collections import defaultdict
import locale
import logging

# Import schema classes untuk dashboard data
from ..schemas.dashboard import DashboardData, ChartData, RevenueSummary, StatCard, InvoiceSummary

# Atur logger
logger = logging.getLogger(__name__)


# Impor model dengan nama yang akan kita gunakan secara konsisten
from ..models import (
    Invoice,
    Pelanggan,
    HargaLayanan,
    MikrotikServer,
    PaketLayanan,
    Langganan,
    DataTeknis,
    TroubleTicket,
)
from sqlalchemy.orm import selectinload
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel

from ..auth import get_current_active_user
from ..database import get_db, get_connection_pool_status, monitor_connection_pool
from ..services import mikrotik_service
from ..services.cache_service import get_cache_stats, clear_all_cache
from ..middleware.query_timeout import execute_with_timeout, get_query_limit, validate_query_limit

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


async def _get_revenue_summary(db: AsyncSession) -> RevenueSummary:
    """Helper untuk mengambil ringkasan pendapatan bulanan - OPTIMIZED VERSION."""
    # PERFORMANCE NOTE: This query needs indexes on:
    # - invoices(paid_at)
    # - invoices(status_invoice)
    # - pelanggan(id_brand)
    now = datetime.now()
    # OPTIMIZATION: Use date range instead of func.extract() for better performance
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if now.month == 12:
        end_of_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        end_of_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

    revenue_stmt = (
        select(HargaLayanan.brand, func.sum(Invoice.total_harga).label("total_revenue"))
        .select_from(Invoice)
        .join(Pelanggan, Invoice.pelanggan_id == Pelanggan.id, isouter=True)
        .join(HargaLayanan, Pelanggan.id_brand == HargaLayanan.id_brand, isouter=True)
        .where(
            Invoice.status_invoice == "Lunas",
            HargaLayanan.brand.is_not(None),
            Invoice.paid_at >= start_of_month,
            Invoice.paid_at < end_of_month,
        )
        .group_by(HargaLayanan.brand)
    )
    revenue_results = (await db.execute(revenue_stmt)).all()
    brand_breakdown = [BrandRevenueItem(brand=row.brand, revenue=float(row.total_revenue or 0.0)) for row in revenue_results]
    total_revenue = sum(item.revenue for item in brand_breakdown)
    next_month_date = now + relativedelta(months=1)
    periode_str = next_month_date.strftime("%B %Y")

    return RevenueSummary(total=total_revenue, periode=periode_str, breakdown=brand_breakdown)


async def _get_pelanggan_stat_cards(db: AsyncSession) -> List[StatCard]:
    """Helper untuk mengambil data kartu statistik pelanggan."""
    pelanggan_count_stmt = (
        select(HargaLayanan.brand, func.count(Pelanggan.id))
        .join(Pelanggan, HargaLayanan.id_brand == Pelanggan.id_brand, isouter=True)
        .group_by(HargaLayanan.brand)
    )
    pelanggan_counts = (await db.execute(pelanggan_count_stmt)).all()
    pelanggan_by_brand = {brand.lower(): count for brand, count in pelanggan_counts}

    return [
        StatCard(
            title="Jumlah Pelanggan Jakinet",
            value=pelanggan_by_brand.get("jakinet", 0),
            description="Total Pelanggan Jakinet",
        ),
        StatCard(
            title="Jumlah Pelanggan Jelantik",
            value=pelanggan_by_brand.get("jelantik", 0),
            description="Total Pelanggan Jelantik",
        ),
        StatCard(
            title="Pelanggan Jelantik Nagrak",
            value=pelanggan_by_brand.get("jelantik nagrak", 0),
            description="Total Pelanggan Rusun Nagrak",
        ),
    ]


async def _get_loyalty_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data chart loyalitas pembayaran - SAFE VERSION."""

    # Get outstanding payers
    outstanding_payers_sq = (
        select(Invoice.pelanggan_id).where(Invoice.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"])).distinct()
    )

    # Get ever late payers
    ever_late_payers_sq = select(Invoice.pelanggan_id).where(Invoice.paid_at > Invoice.tgl_jatuh_tempo).distinct()

    # Simplified query using EXISTS for better compatibility
    categorization_stmt = (
        select(
            func.count(Langganan.id).label("total_active"),
        )
        .select_from(Langganan)
        .where(Langganan.status == "Aktif")
    )

    total_active = (await db.execute(categorization_stmt)).scalar() or 0

    # Get counts using separate, simpler queries
    outstanding_count_stmt = select(func.count(Langganan.id)).where(
        Langganan.status == "Aktif", Langganan.pelanggan_id.in_(outstanding_payers_sq)
    )

    ever_late_count_stmt = select(func.count(Langganan.id)).where(
        Langganan.status == "Aktif",
        Langganan.pelanggan_id.in_(ever_late_payers_sq),
        ~Langganan.pelanggan_id.in_(outstanding_payers_sq),
    )

    outstanding_count = (await db.execute(outstanding_count_stmt)).scalar() or 0
    ever_late_count = (await db.execute(ever_late_count_stmt)).scalar() or 0
    setia_count = total_active - outstanding_count - ever_late_count

    return ChartData(
        labels=["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"],
        data=[
            max(0, setia_count),
            max(0, ever_late_count),
            max(0, outstanding_count),
        ],
    )


async def _get_mikrotik_status_counts(db: AsyncSession) -> dict:
    """Helper untuk memeriksa status online/offline semua server Mikrotik secara paralel."""
    all_servers = (await db.execute(select(MikrotikServer))).scalars().all()
    if not all_servers:
        return {"online": 0, "offline": 0, "total": 0}

    async def check_status(server):
        loop = asyncio.get_event_loop()
        api, conn = None, None
        try:
            # PERFORMANCE FIX: Pakai timeout 8 detik (lebih aman untuk koneksi awal/remote)
            api, conn = await asyncio.wait_for(
                loop.run_in_executor(None, mikrotik_service.get_api_connection, server),
                timeout=8.0
            )
            if conn:
                try:
                    mikrotik_service.mikrotik_pool.return_connection(conn, server.host_ip, int(server.port))
                except:
                    pass
            return api is not None
        except Exception:
            # Jika timeout atau error, kembalikan ke pool jika sempat terbuka
            if conn:
                try:
                    mikrotik_service.mikrotik_pool.return_connection(conn, server.host_ip, int(server.port))
                except:
                    pass
            return False

    results = await asyncio.gather(*(check_status(server) for server in all_servers))
    online_count = sum(1 for res in results if res)
    return {
        "online": online_count,
        "offline": len(all_servers) - online_count,
        "total": len(all_servers),
    }


# In-memory cache untuk Mikrotik status — hindari koneksi TCP berulang ke router setiap kali dashboard dibuka
_mikrotik_cache = {"data": None, "timestamp": 0}
_mikrotik_cache_duration = 180  # 3 menit cache
_is_refreshing_mikrotik = False  # Flag biar gak refresh berkali-kali barengan


# Lock global untuk mencegah race condition saat refresh status Mikrotik
_mikrotik_lock = asyncio.Lock()

async def _get_mikrotik_status_counts_cached(db: AsyncSession) -> dict:
    """Cached wrapper dengan teknik Stale-While-Revalidate dan Race Condition Protection."""
    global _mikrotik_cache
    current_time = time.time()
    
    # 1. Jika cache ada dan masih segar, langsung kirim
    if _mikrotik_cache["data"]:
        age = current_time - _mikrotik_cache["timestamp"]
        if age < _mikrotik_cache_duration:
            return _mikrotik_cache["data"]
        
        # 2. Jika stale, refresh di background (jangan ditunggu)
        # Tapi hanya jalankan 1 refresh saja
        if not _mikrotik_lock.locked():
             all_servers = (await db.execute(select(MikrotikServer))).scalars().all()
             server_list = [{"host_ip": s.host_ip, "port": s.port} for s in all_servers]
             asyncio.create_task(_refresh_mikrotik_status_bg(server_list))
             
        return _mikrotik_cache["data"]

    # 3. COLD BOOT (Cache Kosong): Semua request WAJIB antri di Lock
    # Ini memastikan kita cuma cek router 1x dan semua request dapat data asli.
    async with _mikrotik_lock:
        # Cek lagi siapa tahu sudah diisi oleh request sebelumnya yang antri
        if _mikrotik_cache["data"]:
            return _mikrotik_cache["data"]
            
        # Ambil data dari DB
        all_servers = (await db.execute(select(MikrotikServer))).scalars().all()
        server_list = [{"host_ip": s.host_ip, "port": s.port} for s in all_servers]
        
        # Lakukan pengecekan sekarang (tunggu selesai)
        await _refresh_mikrotik_status_logic(server_list)
        return _mikrotik_cache["data"]


async def _refresh_mikrotik_status_bg(server_list: list):
    """Fungsi pembungkus untuk background task (pakai lock)."""
    async with _mikrotik_lock:
        await _refresh_mikrotik_status_logic(server_list)


async def _refresh_mikrotik_status_logic(server_list: list):
    """Logika inti pengecekan status via TCP Socket."""
    global _mikrotik_cache
    try:
        async def check_online_fast(host, port):
            try:
                future = asyncio.open_connection(host, port)
                reader, writer = await asyncio.wait_for(future, timeout=3.0)
                writer.close()
                try: await writer.wait_closed()
                except: pass
                return True
            except:
                return False

        results = await asyncio.gather(*(
            check_online_fast(s['host_ip'], int(s['port'])) for s in server_list
        ))
        
        online = sum(1 for r in results if r)
        total = len(server_list)
        
        _mikrotik_cache["data"] = {
            "online": online,
            "offline": max(0, total - online),
            "total": total
        }
        _mikrotik_cache["timestamp"] = time.time()
        logger.info(f"📊 Mikrotik Status Sync: {online} Online, {total - online} Offline")
    except Exception as e:
        logger.error(f"❌ Mikrotik status logic failed: {e}")


def clear_mikrotik_cache():
    """Clear mikrotik status cache."""
    global _mikrotik_cache
    _mikrotik_cache = {"data": None, "timestamp": 0}


class MikrotikStatus(BaseModel):
    online: int
    offline: int


async def _get_lokasi_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data chart pelanggan per lokasi."""
    lokasi_stmt = (
        select(Pelanggan.alamat, func.count(Pelanggan.id))
        .where(Pelanggan.alamat.isnot(None))
        .group_by(Pelanggan.alamat)
        .order_by(func.count(Pelanggan.id).desc())
        .limit(15)
    )
    lokasi_data = (await db.execute(lokasi_stmt)).all()
    return ChartData(
        labels=[item[0] for item in lokasi_data if item[0] is not None],
        data=[item[1] for item in lokasi_data if item[0] is not None],
    )


async def _get_paket_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data chart pelanggan per paket."""
    paket_stmt = (
        select(PaketLayanan.kecepatan, func.count(Langganan.id))
        .join(Langganan, PaketLayanan.id == Langganan.paket_layanan_id, isouter=True)
        .where(Langganan.status == "Aktif")
        .group_by(PaketLayanan.kecepatan)
        .order_by(PaketLayanan.kecepatan)
        .limit(10)
    )
    paket_data = (await db.execute(paket_stmt)).all()
    return ChartData(
        labels=[f"{item[0]} Mbps" for item in paket_data],
        data=[item[1] for item in paket_data],
    )


async def _get_growth_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data chart tren pertumbuhan pelanggan."""
    two_years_ago = datetime.now() - relativedelta(years=2)
    growth_stmt = (
        select(
            func.year(Pelanggan.tgl_instalasi).label("year"),
            func.month(Pelanggan.tgl_instalasi).label("month"),
            func.count(Pelanggan.id).label("jumlah"),
        )
        .where(Pelanggan.tgl_instalasi >= two_years_ago)
        .group_by(func.year(Pelanggan.tgl_instalasi), func.month(Pelanggan.tgl_instalasi))
        .order_by(func.year(Pelanggan.tgl_instalasi), func.month(Pelanggan.tgl_instalasi))
    )
    growth_data = (await db.execute(growth_stmt)).all()
    return ChartData(
        labels=[datetime(item.year, item.month, 1).strftime("%b %Y") for item in growth_data],
        data=[item.jumlah for item in growth_data],
    )


async def _get_invoice_summary_chart(db: AsyncSession) -> Optional[InvoiceSummary]:
    """Helper untuk mengambil data ringkasan invoice bulanan."""
    six_months_ago = datetime.now() - timedelta(days=180)
    invoice_stmt = (
        select(
            func.year(Invoice.tgl_invoice).label("year"),
            func.month(Invoice.tgl_invoice).label("month"),
            func.count(Invoice.id).label("total"),
            func.sum(case((Invoice.status_invoice == "Lunas", 1), else_=0)).label("lunas"),
            func.sum(case((Invoice.status_invoice == "Belum Dibayar", 1), else_=0)).label("menunggu"),
            func.sum(case((Invoice.status_invoice == "Expired", 1), else_=0)).label("kadaluarsa"),
            func.sum(case((Invoice.invoice_type == "automatic", 1), else_=0)).label("otomatis"),
            func.sum(case((Invoice.invoice_type == "manual", 1), else_=0)).label("manual_invoice"),
            func.sum(case((Invoice.is_reinvoice == True, 1), else_=0)).label("reinvoice"),
        )
        .where(Invoice.tgl_invoice >= six_months_ago)
        .where(Invoice.deleted_at.is_(None))
        .group_by(func.year(Invoice.tgl_invoice), func.month(Invoice.tgl_invoice))
        .order_by(func.year(Invoice.tgl_invoice), func.month(Invoice.tgl_invoice))
    )
    invoice_data = (await db.execute(invoice_stmt)).all()

    if not invoice_data:
        # Fallback chart data
        now = datetime.now()
        labels = [(now - relativedelta(months=i)).strftime("%b %Y") for i in range(5, -1, -1)]
        return InvoiceSummary(
            labels=labels,
            total=[0] * 6,
            lunas=[0] * 6,
            menunggu=[0] * 6,
            kadaluarsa=[0] * 6,
            otomatis=[0] * 6,
            manual=[0] * 6,
            reinvoice=[0] * 6
        )

    return InvoiceSummary(
        labels=[datetime(item.year, item.month, 1).strftime("%b %Y") for item in invoice_data],
        total=[item.total or 0 for item in invoice_data],
        lunas=[item.lunas or 0 for item in invoice_data],
        menunggu=[item.menunggu or 0 for item in invoice_data],
        kadaluarsa=[item.kadaluarsa or 0 for item in invoice_data],
        otomatis=[item.otomatis or 0 for item in invoice_data],
        manual=[item.manual_invoice or 0 for item in invoice_data],
        reinvoice=[item.reinvoice or 0 for item in invoice_data],
    )


async def _get_status_langganan_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data status langganan."""
    status_stmt = (
        select(Langganan.status, func.count(Langganan.id).label("jumlah"))
        .group_by(Langganan.status)
        .order_by(Langganan.status)
    )
    status_results = (await db.execute(status_stmt)).all()
    return ChartData(
        labels=[row.status for row in status_results],
        data=[row.jumlah for row in status_results],
    )


async def _get_pelanggan_per_alamat_chart(db: AsyncSession) -> ChartData:
    """Helper untuk mengambil data pelanggan aktif per alamat."""
    alamat_stmt = (
        select(Pelanggan.alamat, func.count(Pelanggan.id).label("jumlah"))
        .join(Langganan, Pelanggan.id == Langganan.pelanggan_id)
        .where(Langganan.status == "Aktif")
        .group_by(Pelanggan.alamat)
        .order_by(func.count(Pelanggan.id).desc())
        .limit(20)
    )
    alamat_results = (await db.execute(alamat_stmt)).all()
    return ChartData(
        labels=[row.alamat for row in alamat_results],
        data=[row.jumlah for row in alamat_results],
    )


@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Get dashboard data with parallel query execution and caching headers.
    """
    # OPTIMIZATION: Browser/Proxy caching (5 menit)
    response.headers["Cache-Control"] = "public, max-age=300" 
    
    start_time = time.time()

    try:
        user_with_role = await db.execute(
            select(UserModel)
            .options(selectinload(UserModel.role).selectinload(RoleModel.permissions))
            .where(UserModel.id == current_user.id)
        )
        user = user_with_role.scalar_one_or_none()

        if not user or not user.role:
            return DashboardData()

        user_permissions = {p.name for p in user.role.permissions}
        dashboard_response = DashboardData()

        # --- OPTIMISASI: Jalankan SEMUA pengambilan data secara paralel ---
        tasks = {}

        if "view_widget_pendapatan_bulanan" in user_permissions:
            tasks["revenue_summary"] = asyncio.create_task(_get_revenue_summary(db))

        if "view_widget_statistik_pelanggan" in user_permissions:
            tasks["pelanggan_stats"] = asyncio.create_task(_get_pelanggan_stat_cards(db))
            tasks["loyalty_chart"] = asyncio.create_task(_get_loyalty_chart(db))

        if "view_widget_statistik_server" in user_permissions:
            tasks["server_stats"] = asyncio.create_task(_get_mikrotik_status_counts_cached(db))

        if "view_widget_pelanggan_per_lokasi" in user_permissions:
            tasks["lokasi_chart"] = asyncio.create_task(_get_lokasi_chart(db))

        if "view_widget_pelanggan_per_paket" in user_permissions:
            tasks["paket_chart"] = asyncio.create_task(_get_paket_chart(db))

        if "view_widget_tren_pertumbuhan" in user_permissions:
            tasks["growth_chart"] = asyncio.create_task(_get_growth_chart(db))

        # View Invoice Widget (Always true/base permission)
        tasks["invoice_summary_chart"] = asyncio.create_task(_get_invoice_summary_chart(db))

        if "view_widget_status_langganan" in user_permissions:
            tasks["status_langganan_chart"] = asyncio.create_task(_get_status_langganan_chart(db))

        if "view_widget_alamat_aktif" in user_permissions:
            tasks["pelanggan_per_alamat_chart"] = asyncio.create_task(_get_pelanggan_per_alamat_chart(db))

        # Jalankan semua task secara paralel
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            results_map = dict(zip(tasks.keys(), results))

            # --- Mapping Hasil ke dashboard_response ---
            
            # Helper untuk cek error
            def get_res(key):
                res = results_map.get(key)
                if isinstance(res, Exception):
                    logger.error(f"Error fetching {key}: {res}")
                    return None
                return res

            dashboard_response.revenue_summary = get_res("revenue_summary")
            dashboard_response.loyalitas_pembayaran_chart = get_res("loyalty_chart")
            dashboard_response.lokasi_chart = get_res("lokasi_chart")
            dashboard_response.paket_chart = get_res("paket_chart")
            dashboard_response.growth_chart = get_res("growth_chart")
            dashboard_response.invoice_summary_chart = get_res("invoice_summary_chart")
            dashboard_response.status_langganan_chart = get_res("status_langganan_chart")
            dashboard_response.pelanggan_per_alamat_chart = get_res("pelanggan_per_alamat_chart")

            # Stat Cards Assembly
            temp_stat_cards = []
            pelanggan_stats = get_res("pelanggan_stats")
            if pelanggan_stats: temp_stat_cards.extend(pelanggan_stats)

            server_stats = get_res("server_stats")
            if server_stats:
                temp_stat_cards.extend([
                    StatCard(title="Total Servers", value=server_stats.get("total", 0), description="Total Mikrotik servers"),
                    StatCard(title="Online Servers", value=server_stats.get("online", 0), description="Servers online"),
                    StatCard(title="Offline Servers", value=server_stats.get("offline", 0), description="Servers offline"),
                ])
            
            dashboard_response.stat_cards = temp_stat_cards

        execution_time = time.time() - start_time
        if execution_time > 2.0:
            logger.warning(f"⚠️ Dashboard response took {execution_time:.2f}s")
        
        return dashboard_response

    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(f"❌ Dashboard failed after {execution_time:.2f}s: {str(e)}", exc_info=True)
        # Fallback response (empty) to avoid 500 errors
        return DashboardData(
            revenue_summary=RevenueSummary(total=0.0, periode="bulan", breakdown=[]),
            stat_cards=[],
            lokasi_chart=ChartData(labels=[], data=[]),
            paket_chart=ChartData(labels=[], data=[]),
            growth_chart=ChartData(labels=[], data=[]),
            invoice_summary_chart=InvoiceSummary(labels=[], total=[], lunas=[], menunggu=[], kadaluarsa=[]),
            status_langganan_chart=ChartData(labels=[], data=[]),
            pelanggan_per_alamat_chart=ChartData(labels=[], data=[]),
            loyalitas_pembayaran_chart=ChartData(labels=[], data=[]),
        )



class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int
    total_invoice_count: int
    open_tickets_count: int


# Menambahkan ini ke file dashboard.py di router dashboard


@router.get("/loyalitas-users-by-segment")
async def get_loyalty_users_by_segment(segmen: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Mengambil daftar user berdasarkan segmen loyalitas pembayaran secara efisien
    tanpa N+1 query.
    """
    try:
        # OPTIMIZED: Single query dengan aggregation untuk menggantikan 3 query terpisah
        loyalty_query = select(
            Pelanggan.id,
            Pelanggan.nama,
            Pelanggan.alamat,
            Pelanggan.no_telp,
            DataTeknis.id_pelanggan,
            func.sum(
                case(
                    (Invoice.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"]), 1),
                    else_=0
                )
            ).label("outstanding_count"),
            func.sum(
                case(
                    (Invoice.paid_at > Invoice.tgl_jatuh_tempo, 1),
                    else_=0
                )
            ).label("late_count"),
        ).select_from(
            Pelanggan
        ).join(
            Langganan, Pelanggan.id == Langganan.pelanggan_id
        ).outerjoin(
            Invoice, Pelanggan.id == Invoice.pelanggan_id
        ).outerjoin(
            DataTeknis, Pelanggan.id == DataTeknis.pelanggan_id
        ).where(
            Langganan.status == "Aktif"
        ).group_by(
            Pelanggan.id, Pelanggan.nama, Pelanggan.alamat, Pelanggan.no_telp, DataTeknis.id_pelanggan
        )

        loyalty_result = await db.execute(loyalty_query)
        loyalty_data = loyalty_result.all()

        # Filter hasil berdasarkan segment yang diminta
        filtered_customers = []
        for row in loyalty_data:
            outstanding_count = row.outstanding_count or 0
            late_count = row.late_count or 0

            is_outstanding = outstanding_count > 0
            is_ever_late = late_count > 0

            # Kategorisasi customer
            if segmen == "Menunggak" and is_outstanding:
                pass  # Include outstanding customers
            elif segmen == "Lunas (Tapi Telat)" and not is_outstanding and is_ever_late:
                pass  # Include paid but late customers
            elif segmen == "Setia On-Time" and not is_outstanding and not is_ever_late:
                pass  # Include on-time customers
            else:
                continue  # Skip customers yang tidak match segment

            # Format response data
            filtered_customers.append({
                "id": row.id,
                "nama": row.nama,
                "id_pelanggan": (row.id_pelanggan if row.id_pelanggan else f"PLG-{row.id:04d}"),
                "alamat": row.alamat or "Alamat tidak tersedia",
                "no_telp": row.no_telp or "Nomor tidak tersedia",
            })

        return filtered_customers
    except Exception as e:
        import traceback

        print(f"Error in loyalitas users: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Gagal mengambil data user loyalitas: {str(e)}")


# Simple in-memory cache untuk sidebar badges
_sidebar_cache = {"data": None, "timestamp": 0}
_cache_duration = 60  # 60 seconds cache

@router.get("/sidebar-badges", response_model=SidebarBadgeResponse)
async def get_sidebar_badges(db: AsyncSession = Depends(get_db)):
    import time

    # Check cache dulu untuk performance
    current_time = time.time()
    if (_sidebar_cache["data"] and
        current_time - _sidebar_cache["timestamp"] < _cache_duration):
        return _sidebar_cache["data"]

    # Jika cache expired, generate data baru
    # PERBAIKAN: Menggunakan nama 'Langganan' dan 'Invoice'
    suspended_query = select(func.count(Langganan.id)).where(Langganan.status == "Suspended")
    suspended_result = await db.execute(suspended_query)
    suspended_count = suspended_result.scalar_one_or_none() or 0

    # PERBAIKAN: Exclude invoice dengan payment link expired
    # Logic yang sama dengan Invoice.get_payment_link_status()
    # PERFORMANCE FIX: Hitung langsung di database — hindari load semua invoice ke RAM
    from datetime import date
    today = date.today()

    # Query yang menghitung invoice "Belum Dibayar" dengan payment link masih aktif
    # Logika expiry: tanggal 4 bulan berikutnya setelah tgl_invoice
    # Link aktif jika today <= expiry_date
    # Equivalent SQL: WHERE tgl_invoice >= (first day of current month - 4 days)
    # Artinya: invoice yang tgl_invoice-nya di bulan lalu atau lebih baru masih aktif di tanggal 4 bulan ini
    active_cutoff = date(today.year, today.month, 1) - timedelta(days=4)
    # Lebih tepat: invoice aktif jika tanggal 4 bulan setelah tgl_invoice >= today
    # Menggunakan pendekatan: filter invoice yang bulan tgl_invoice >= (bulan sekarang - 1)
    # Karena expiry = tanggal 4 bulan depan dari tgl_invoice

    active_unpaid_query = (
        select(func.count(Invoice.id))
        .where(
            Invoice.status_invoice == "Belum Dibayar",
            # Expiry date = tanggal 4 bulan berikutnya setelah tgl_invoice
            # Invoice aktif jika today <= expiry_date
            # Setara dengan: tgl_invoice >= tanggal 5 bulan lalu (approx)
            # Gunakan pendekatan konservatif: ambil invoice dari 2 bulan terakhir
            # dan biarkan cache 60 detik menangani sisanya
            Invoice.tgl_invoice >= date(
                today.year if today.month > 1 else today.year - 1,
                today.month - 1 if today.month > 1 else 12,
                1
            )
        )
    )
    active_unpaid_result = await db.execute(active_unpaid_query)
    active_unpaid_count = active_unpaid_result.scalar_one_or_none() or 0

    # Untuk logging, hitung total unpaid juga
    total_unpaid_query = select(func.count(Invoice.id)).where(Invoice.status_invoice == "Belum Dibayar")
    total_unpaid_result = await db.execute(total_unpaid_query)
    total_unpaid = total_unpaid_result.scalar_one_or_none() or 0
    expired_count = total_unpaid - active_unpaid_count

    logger.info(f"Unpaid invoice stats - Total: {total_unpaid}, Active: {active_unpaid_count}, Expired: {expired_count}")

    unpaid_count = active_unpaid_count

    stopped_query = select(func.count(Langganan.id)).where(Langganan.status == "Berhenti")
    stopped_result = await db.execute(stopped_query)
    stopped_count = stopped_result.scalar_one_or_none() or 0

    total_invoice_query = select(func.count(Invoice.id)).where(Invoice.deleted_at.is_(None))
    total_invoice_result = await db.execute(total_invoice_query)
    total_invoice_count = total_invoice_result.scalar_one_or_none() or 0

    open_tickets_query = select(func.count(TroubleTicket.id)).where(TroubleTicket.status == "Open")
    open_tickets_result = await db.execute(open_tickets_query)
    open_tickets_count = open_tickets_result.scalar_one_or_none() or 0

    # Generate response dan cache
    response_data = SidebarBadgeResponse(
        suspended_count=suspended_count,
        unpaid_invoice_count=unpaid_count,
        stopped_count=stopped_count,
        total_invoice_count=total_invoice_count,
        open_tickets_count=open_tickets_count,
    )

    # Simpan ke cache
    _sidebar_cache["data"] = response_data
    _sidebar_cache["timestamp"] = current_time

    return response_data


# Function untuk clear sidebar cache (dipanggil dari invoice callback)
def clear_sidebar_cache():
    """Clear sidebar badge cache when invoice status changes."""
    global _sidebar_cache
    _sidebar_cache = {"data": None, "timestamp": 0}


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

    # Gunakan dict standar untuk kejelasan tipe
    paket_details: Dict[str, Dict[str, Any]] = {}

    for kecepatan, alamat, brand, jumlah in raw_data:
        if not alamat or not brand:
            continue

        paket_key = f"{kecepatan} Mbps"

        # Inisialisasi struktur data jika belum ada
        if paket_key not in paket_details:
            paket_details[paket_key] = {
                "total_pelanggan": 0,
                "lokasi": {},
                "brand": {},
            }

        details = paket_details[paket_key]

        details["total_pelanggan"] += jumlah
        # Inkrementasi jumlah untuk lokasi dan brand secara manual
        details["lokasi"][alamat] = details["lokasi"].get(alamat, 0) + jumlah
        details["brand"][brand] = details["brand"].get(brand, 0) + jumlah

    final_response = {}
    for paket_key, details in paket_details.items():
        sorted_lokasi = sorted(details.get("lokasi", {}).items(), key=lambda item: item[1], reverse=True)
        sorted_brand = sorted(details.get("brand", {}).items(), key=lambda item: item[1], reverse=True)

        final_response[paket_key] = PaketDetail(
            total_pelanggan=int(details.get("total_pelanggan", 0)),
            breakdown_lokasi=[BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_lokasi],
            breakdown_brand=[BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_brand],
        )

    return final_response


@router.get("/database-health")
async def get_database_health(current_user: UserModel = Depends(get_current_active_user)):
    """
    Get database connection pool status for monitoring dashboard performance.
    Only accessible to authenticated users.
    """
    try:
        pool_status = await get_connection_pool_status()
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "connection_pool": pool_status,
            "performance_impact": {
                "healthy_connections": pool_status["checked_in"],
                "active_connections": pool_status["checked_out"],
                "available_connections": pool_status["pool_size"] - pool_status["checked_out"],
                "utilization_percent": round(
                    (pool_status["checked_out"] / (pool_status["pool_size"] + pool_status["overflow"])) * 100, 2
                ),
            },
        }
    except Exception as e:
        return {"status": "error", "timestamp": datetime.now().isoformat(), "error": str(e), "connection_pool": None}


@router.get("/api-performance", response_model=dict)
async def get_api_performance_metrics(response: Response, current_user: UserModel = Depends(get_current_active_user)):
    """
    Get API response performance metrics for monitoring.
    API Response Optimization: Performance tracking endpoint.
    """
    # API Response Optimization: Add cache headers
    response.headers["Cache-Control"] = "public, max-age=60"  # 1 minute cache

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "optimization_features": {
            "gzip_compression": "enabled (min_size: 1KB)",
            "field_filtering": "enabled (pelanggan endpoint)",
            "cache_headers": "enabled (5-300s TTL)",
            "response_monitoring": "enabled",
            "in_memory_cache": "enabled (LRU eviction)",
        },
        "performance_tips": [
            "Use ?fields=id,nama,email untuk field filtering di pelanggan endpoint",
            "Dashboard data di-cache selama 5 menit",
            "Response > 50KB otomatis di-compress",
            "Monitor X-Response-Size headers di browser DevTools",
            "Static data (harga_layanan, paket_layanan) di-cache 1 jam",
        ],
        "optimization_impact": {
            "estimated_size_reduction": "30-70%",
            "estimated_speed_improvement": "40-80%",
            "bandwidth_savings": "Significant untuk large datasets",
            "database_load_reduction": "60-90% untuk static data",
        },
    }


@router.get("/cache-stats", response_model=dict)
async def get_cache_statistics(
    response: Response,
    current_user: UserModel = Depends(get_current_active_user),
    clear_cache: bool = Query(False, description="Clear all cache data"),
):
    """
    Get cache statistics untuk monitoring cache performance.
    Cache Strategy: Cache monitoring dan management endpoint.
    """
    # Cache Strategy: Add cache headers
    response.headers["Cache-Control"] = "public, max-age=30"  # 30 detik cache

    if clear_cache:
        cleared_count = clear_all_cache()
        return {
            "status": "success",
            "action": "cache_cleared",
            "cleared_items": cleared_count,
            "timestamp": datetime.now().isoformat(),
        }

    cache_stats = get_cache_stats()

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "cache_statistics": cache_stats,
        "cache_configuration": {
            "harga_layanan_ttl": "1 jam",
            "paket_layanan_ttl": "1 jam",
            "brand_data_ttl": "30 menit",
            "mikrotik_servers_ttl": "5 menit",
            "user_permissions_ttl": "10 menit",
            "dashboard_cache_ttl": "5 menit",
            "max_cache_size": 1000,
        },
        "cache_health": {
            "hit_rate_status": (
                "Excellent"
                if cache_stats["hit_rate_percent"] > 80
                else "Good" if cache_stats["hit_rate_percent"] > 60 else "Needs Improvement"
            ),
            "memory_usage": "Healthy" if cache_stats["utilization_percent"] < 80 else "High",
        },
    }


@router.get("/websocket-metrics", response_model=dict)
async def get_websocket_metrics(
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get WebSocket performance metrics untuk monitoring.
    WebSocket Performance: Real-time connection monitoring dan analytics.
    """
    from ..websocket_manager import manager
    from datetime import datetime

    metrics = manager.get_metrics()

    return {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "websocket_metrics": metrics,
        "performance_analysis": {
            "connection_health": "Excellent" if metrics["active_connections"] > 0 else "No connections",
            "message_success_rate": (
                "Excellent"
                if metrics["success_rate"] > 95
                else "Good" if metrics["success_rate"] > 85 else "Needs Improvement"
            ),
            "response_performance": (
                "Excellent"
                if metrics["avg_response_time_ms"] < 50
                else "Good" if metrics["avg_response_time_ms"] < 100 else "Slow"
            ),
            "connection_stability": "Stable" if metrics["avg_connection_duration_min"] > 5 else "New",
        },
        "optimization_features": {
            "heartbeat_enabled": True,
            "batch_processing": True,
            "connection_pooling": True,
            "role_based_broadcasting": True,
            "automatic_cleanup": True,
        },
    }


# ====================================================================
# INVOICE GENERATION MONITORING WIDGET
# ====================================================================

@router.get("/invoice-generation-monitor")
async def get_invoice_generation_monitor(
    target_date: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Widget dashboard untuk monitoring invoice generation.
    Menampilkan summary skipped invoices untuk bulan depan atau tanggal spesifik.

    Required roles: superadmin, admin, manager
    """
    from ..config import settings

    # Check user permissions using config
    # Handle both string role and Role object
    user_role_name = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
    if not settings.can_access_widget("invoice_generation_monitor", user_role_name):
        raise HTTPException(
            status_code=403,
            detail="Anda tidak memiliki izin untuk mengakses widget monitoring invoice"
        )

    from datetime import date, timedelta

    # Calculate smart target date if not provided
    # RULE: Monitor targets the most recently started/finished run.
    # If today >= H-5 of Month M+1, then M+1 is current (we monitor it).
    # Else, Month M is current.
    if target_date:
        target_date_obj = date.fromisoformat(target_date)
    else:
        from datetime import date as date_type
        today = date_type.today()
        # M = 1st of this month
        m = today.replace(day=1)
        # M+1 = 1st of next month
        if m.month == 12:
            m_plus_1 = date_type(m.year + 1, 1, 1)
        else:
            m_plus_1 = date_type(m.year, m.month + 1, 1)
        
        # Generation for M+1 happens on M+1 minus 5 days
        # We also consider time (13:00) but date check is usually enough for dashboard default
        gen_date_m_plus_1 = m_plus_1 - timedelta(days=5)
        
        if today >= gen_date_m_plus_1:
            target_date_obj = m_plus_1
        else:
            target_date_obj = m

    # Get langganan yang seharusnya dapat invoice
    should_have_stmt = (
        select(func.count(Langganan.id))
        .where(
            Langganan.tgl_jatuh_tempo == target_date_obj,
            Langganan.status == "Aktif"
        )
    )
    total_should_have = (await db.execute(should_have_stmt)).scalar() or 0

    # Get invoice yang sudah di-generate untuk periode ini
    target_year, target_month = target_date_obj.year, target_date_obj.month
    start_of_month = date(target_year, target_month, 1)
    if target_month == 12:
        end_of_month = date(target_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(target_year, target_month + 1, 1) - timedelta(days=1)

    existing_invoices_stmt = (
        select(func.count(func.distinct(Invoice.pelanggan_id)))
        .where(Invoice.tgl_jatuh_tempo.between(start_of_month, end_of_month))
    )
    total_generated = (await db.execute(existing_invoices_stmt)).scalar() or 0

    total_skipped = total_should_have - total_generated
    success_rate = round((total_generated / total_should_have * 100) if total_should_have > 0 else 100, 1)

    # Status Determination
    now = datetime.now()
    today = now.date()
    generation_date = target_date_obj - timedelta(days=5)
    # Jadwal generate adalah jam 13:00 (1 siang)
    generation_hour = 13

    if total_skipped == 0:
        status, status_color, status_icon = "HEALTHY", "success", "✅"
        message = f"{status_icon} Semua invoice berhasil di-generate"
    elif today < generation_date or (today == generation_date and now.hour < generation_hour):
        # Sebelum jadwal: Jangan tampilkan statistik sebagai "hasil" dulu agar tidak menyesatkan
        status, status_color, status_icon = "UPCOMING", "info", "🕒"
        
        # Reset hasil sementara (manual) ke 0 untuk monitor otomatis agar tidak membingungkan
        total_generated = 0 
        total_skipped = 0 
        success_rate = 0.0
        
        # Format date manually to ensure Indonesian
        months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        gen_month_name = months[generation_date.month - 1]
        gen_date_str = f"{generation_date.day} {gen_month_name} {generation_date.year}"
        
        message = f"{status_icon} Menunggu jadwal otomatis hari ini jam {generation_hour}:00 WIB" if today == generation_date else f"{status_icon} Menunggu jadwal generate otomatis pada {gen_date_str} (H-5)"
    elif total_skipped <= 5:
        status, status_color, status_icon = "NEEDS_ATTENTION", "warning", "⚠️"
        message = f"{status_icon} {total_skipped} pelanggan terlewat"
    else:
        status, status_color, status_icon = "CRITICAL", "error", "🔴"
        message = f"{status_icon} {total_skipped} pelanggan terlewat"

    return {
        "target_date": target_date_obj.isoformat(),
        "total_should_have": total_should_have,
        "total_generated": total_generated,
        "total_skipped": total_skipped,
        "success_rate": success_rate,
        "status": status,
        "status_color": status_color,
        "status_icon": status_icon,
        "message": f"{status_icon} {total_skipped} pelanggan terlewat" if total_skipped > 0 else f"{status_icon} Semua invoice berhasil di-generate",
        "detail_url": f"/invoices/skipped-invoice-generation?target_date={target_date_obj.isoformat()}"
    }


@router.get("/future-invoice-projection")
async def get_future_invoice_projection(
    target_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mendapatkan proyeksi invoice untuk tanggal di masa depan.
    Untuk monitoring persiapan sistem.

    Required roles: superadmin, admin, manager
    """
    from ..config import settings

    # Check user permissions using config
    # Handle both string role and Role object
    user_role_name = current_user.role.name if hasattr(current_user.role, 'name') else str(current_user.role)
    if not settings.can_access_widget("future_invoice_projection", user_role_name):
        raise HTTPException(
            status_code=403,
            detail="Anda tidak memiliki izin untuk mengakses widget proyeksi invoice"
        )
    from datetime import date, timedelta

    from datetime import date as date_type
    today = date_type.today()

    # Calculate smart target date if not provided
    # RULE: Projection targets the NEXT upcoming run whose generation hasn't passed.
    if target_date:
        target_date_obj = date.fromisoformat(target_date)
    else:
        # M = 1st of this month
        m = today.replace(day=1)
        # M+1 = 1st of next month
        if m.month == 12:
            m_plus_1 = date_type(m.year + 1, 1, 1)
        else:
            m_plus_1 = date_type(m.year, m.month + 1, 1)
        
        # Gen for M+1 happens on M+1 minus 5 days
        gen_date_m_plus_1 = m_plus_1 - timedelta(days=5)
        
        if today >= gen_date_m_plus_1:
            # If M+1 gen is already done, project for M+2
            if m_plus_1.month == 12:
                target_date_obj = date_type(m_plus_1.year + 1, 1, 1)
            else:
                target_date_obj = date_type(m_plus_1.year, m_plus_1.month + 1, 1)
        else:
            # If M+1 gen is not yet done, project for M+1
            target_date_obj = m_plus_1

    target_date = target_date_obj.isoformat()

    # Hitung hari hingga target date
    days_until = (target_date_obj - today).days if target_date_obj > today else 0

    # Get estimasi pelanggan (yang punya jatuh tempo tanggal yang sama)
    estimated_customers_stmt = (
        select(func.count(Langganan.id))
        .where(
            Langganan.tgl_jatuh_tempo == target_date_obj,
            Langganan.status == "Aktif"
        )
    )
    estimated_customers = (await db.execute(estimated_customers_stmt)).scalar() or 0

    # Get total active customers untuk perhitungan
    total_active_stmt = (
        select(func.count(Langganan.id))
        .where(Langganan.status == "Aktif")
    )
    total_active = (await db.execute(total_active_stmt)).scalar() or 0

    # Calculate projection date (H-5)
    projection_date = target_date_obj - timedelta(days=5)

    # Status sistem logic updated
    now = datetime.now()
    generation_hour = 13

    if today > projection_date or (today == projection_date and now.hour >= generation_hour):
        # Check if invoices have been generated
        # Logic matches invoice-generation-monitor
        target_year, target_month = target_date_obj.year, target_date_obj.month
        start_of_month = date(target_year, target_month, 1)
        if target_month == 12:
            end_of_month = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(target_year, target_month + 1, 1) - timedelta(days=1)

        existing_invoices_stmt = (
            select(func.count(func.distinct(Invoice.pelanggan_id)))
            .where(Invoice.tgl_jatuh_tempo.between(start_of_month, end_of_month))
        )
        total_generated = (await db.execute(existing_invoices_stmt)).scalar() or 0
        
        if total_generated > 0:
            if total_generated >= (estimated_customers * 0.9): # 90% threshold
                system_status = "Selesai"
            else:
                system_status = "Sebagian Selesai"
        else:
             system_status = "Terlewat"
    elif today == projection_date and now.hour < generation_hour:
        system_status = "Menunggu Jadwal"
    else:
        system_status = "Siap" if days_until > 30 else "Persiapan"

    # Hitung hari hingga generation date (H-5)
    generation_days_until = (projection_date - today).days if projection_date > today else 0

    return {
        "target_date": target_date,
        "estimated_customers": estimated_customers,
        "total_active_customers": total_active,
        "days_until": days_until,
        "generation_date": projection_date.isoformat(),
        "generation_days_until": generation_days_until,
        "system_status": system_status,
        "is_future": days_until > 0,
        "percentage_of_active": round((estimated_customers / total_active * 100) if total_active > 0 else 0, 1)
    }
