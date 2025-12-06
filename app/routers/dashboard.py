from fastapi import APIRouter, Depends, HTTPException, Response, Query
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, or_, and_, not_
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio
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
        api, conn = await loop.run_in_executor(None, mikrotik_service.get_api_connection, server)
        if conn:
            conn.disconnect()
        return bool(api)

    results = await asyncio.gather(*(check_status(server) for server in all_servers))
    online_count = sum(1 for res in results if res)
    return {
        "online": online_count,
        "offline": len(all_servers) - online_count,
        "total": len(all_servers),
    }


class MikrotikStatus(BaseModel):
    online: int
    offline: int


@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Get dashboard data with caching headers and error handling.
    API Response Optimization: Cache control untuk mengurangi request frequency.
    """
    # API Response Optimization: Add cache headers untuk 5 menit
    response.headers["Cache-Control"] = "public, max-age=300"

    # PERFORMANCE OPTIMIZATION: Add query timeout monitoring
    import time

    start_time = time.time()

    """
    Get dashboard data with error handling to avoid 500 errors.
    """
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

        # --- OPTIMISASI: Jalankan semua pengambilan data secara paralel dengan error handling ---
        tasks = {}

        if "view_widget_pendapatan_bulanan" in user_permissions:
            tasks["revenue_summary"] = asyncio.create_task(_get_revenue_summary(db))

        if "view_widget_statistik_pelanggan" in user_permissions:
            tasks["pelanggan_stats"] = asyncio.create_task(_get_pelanggan_stat_cards(db))
            tasks["loyalty_chart"] = asyncio.create_task(_get_loyalty_chart(db))

        if "view_widget_statistik_server" in user_permissions:
            tasks["server_stats"] = asyncio.create_task(_get_mikrotik_status_counts(db))

        # Jalankan semua task yang sudah dikumpulkan dengan proper error handling
        if tasks:
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            results_map = dict(zip(tasks.keys(), results))

            # Inisialisasi variabel hasil dengan tipe yang jelas
            revenue_summary_data: Optional[RevenueSummary] = None
            pelanggan_stats_data: Optional[List[StatCard]] = None
            loyalty_chart_data: Optional[ChartData] = None
            server_stats_data: Optional[Dict] = None

            # --- Proses dan validasi tipe setiap hasil secara terpisah ---
            revenue_result = results_map.get("revenue_summary")
            if not isinstance(revenue_result, Exception) and revenue_result is not None:
                revenue_summary_data = revenue_result  # type: ignore
            elif isinstance(revenue_result, Exception):
                logger.error(f"Error fetching revenue summary: {revenue_result}")

            pelanggan_stats_result = results_map.get("pelanggan_stats")
            if not isinstance(pelanggan_stats_result, Exception) and pelanggan_stats_result is not None:
                pelanggan_stats_data = pelanggan_stats_result  # type: ignore
            elif isinstance(pelanggan_stats_result, Exception):
                logger.error(f"Error fetching pelanggan stats: {pelanggan_stats_result}")

            loyalty_chart_result = results_map.get("loyalty_chart")
            if not isinstance(loyalty_chart_result, Exception) and loyalty_chart_result is not None:
                loyalty_chart_data = loyalty_chart_result  # type: ignore
            elif isinstance(loyalty_chart_result, Exception):
                logger.error(f"Error fetching loyalty chart: {loyalty_chart_result}")

            server_stats_result = results_map.get("server_stats")
            if not isinstance(server_stats_result, Exception) and server_stats_result is not None:
                server_stats_data = server_stats_result  # type: ignore
            elif isinstance(server_stats_result, Exception):
                logger.error(f"Error fetching server stats: {server_stats_result}")

            # --- Bangun respons dari variabel yang sudah divalidasi ---
            if revenue_summary_data:
                dashboard_response.revenue_summary = revenue_summary_data

            temp_stat_cards = []
            if pelanggan_stats_data:
                temp_stat_cards.extend(pelanggan_stats_data)

            if server_stats_data:
                server_stats_cards = [
                    StatCard(
                        title="Total Servers",
                        value=server_stats_data.get("total", 0),
                        description="Total Mikrotik servers",
                    ),
                    StatCard(
                        title="Online Servers",
                        value=server_stats_data.get("online", 0),
                        description="Servers currently online",
                    ),
                    StatCard(
                        title="Offline Servers",
                        value=server_stats_data.get("offline", 0),
                        description="Servers currently offline",
                    ),
                ]
                temp_stat_cards.extend(server_stats_cards)

            if loyalty_chart_data:
                dashboard_response.loyalitas_pembayaran_chart = loyalty_chart_data

            if temp_stat_cards:
                dashboard_response.stat_cards = temp_stat_cards

        # --- SISA WIDGET DENGAN ERROR HANDLING ---

        # 3. Widget Chart Pelanggan per Lokasi
        if "view_widget_pelanggan_per_lokasi" in user_permissions:
            try:
                # Optimized: Gunakan index yang sudah ada di model Pelanggan
                lokasi_stmt = (
                    select(Pelanggan.alamat, func.count(Pelanggan.id))
                    .where(Pelanggan.alamat.isnot(None))  # Filter null values
                    .group_by(Pelanggan.alamat)
                    .order_by(func.count(Pelanggan.id).desc())
                    .limit(15)  # Kurangi dari 20 ke 15 untuk lebih cepat
                )
                lokasi_data = (await db.execute(lokasi_stmt)).all()
                dashboard_response.lokasi_chart = ChartData(
                    labels=[item[0] for item in lokasi_data if item[0] is not None],
                    data=[item[1] for item in lokasi_data if item[0] is not None],
                )
            except Exception as e:
                logger.error(f"Dashboard lokasi_chart error: {str(e)}", exc_info=True)
                # Graceful degradation: Set empty chart data
                dashboard_response.lokasi_chart = ChartData(labels=[], data=[])

        # 4. Widget Chart Pelanggan per Paket
        if "view_widget_pelanggan_per_paket" in user_permissions:
            try:
                # Optimized: Filter hanya langganan aktif untuk data yang relevan
                paket_stmt = (
                    select(PaketLayanan.kecepatan, func.count(Langganan.id))
                    .join(Langganan, PaketLayanan.id == Langganan.paket_layanan_id, isouter=True)
                    .where(Langganan.status == "Aktif")  # Hanya yang aktif
                    .group_by(PaketLayanan.kecepatan)
                    .order_by(PaketLayanan.kecepatan)
                    .limit(10)  # Batasi hasil untuk performance
                )
                paket_data = (await db.execute(paket_stmt)).all()
                dashboard_response.paket_chart = ChartData(
                    labels=[f"{item[0]} Mbps" for item in paket_data],
                    data=[item[1] for item in paket_data],
                )
            except Exception as e:
                logger.error(f"Dashboard paket_chart error: {str(e)}", exc_info=True)
                dashboard_response.paket_chart = ChartData(labels=[], data=[])

        # 5. Widget Chart Tren Pertumbuhan Pelanggan
        if "view_widget_tren_pertumbuhan" in user_permissions:
            try:
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
                dashboard_response.growth_chart = ChartData(
                    labels=[datetime(item.year, item.month, 1).strftime("%b %Y") for item in growth_data],
                    data=[item.jumlah for item in growth_data],
                )
            except Exception as e:
                logger.error(f"Dashboard growth_chart error: {str(e)}", exc_info=True)
                dashboard_response.growth_chart = ChartData(labels=[], data=[])

        # 6. Widget Chart Invoice Bulanan
        # Temporary bypass permission check for testing
        if True:  # "view_widget_invoice_bulanan" in user_permissions:
            try:
                six_months_ago = datetime.now() - timedelta(days=180)

                # Query untuk invoice chart - Fixed SQLAlchemy syntax
                invoice_stmt = (
                    select(
                        func.year(Invoice.tgl_invoice).label("year"),
                        func.month(Invoice.tgl_invoice).label("month"),
                        func.count(Invoice.id).label("total"),
                        func.sum(case((Invoice.status_invoice == "Lunas", 1), else_=0)).label("lunas"),
                        func.sum(case((Invoice.status_invoice == "Belum Dibayar", 1), else_=0)).label("menunggu"),
                        func.sum(case((Invoice.status_invoice == "Kadaluarsa", 1), else_=0)).label("kadaluarsa"),
                    )
                    .where(Invoice.tgl_invoice >= six_months_ago)
                    .group_by(func.year(Invoice.tgl_invoice), func.month(Invoice.tgl_invoice))
                    .order_by(func.year(Invoice.tgl_invoice), func.month(Invoice.tgl_invoice))
                )

                invoice_data = (await db.execute(invoice_stmt)).all()

                if invoice_data:
                    dashboard_response.invoice_summary_chart = InvoiceSummary(
                        labels=[datetime(item.year, item.month, 1).strftime("%b %Y") for item in invoice_data],
                        total=[item.total or 0 for item in invoice_data],
                        lunas=[item.lunas or 0 for item in invoice_data],
                        menunggu=[item.menunggu or 0 for item in invoice_data],
                        kadaluarsa=[item.kadaluarsa or 0 for item in invoice_data],
                    )
                    print(f"✅ Invoice chart loaded successfully with {len(invoice_data)} data points")
                else:
                    print("📭 No invoice data found in the last 6 months, creating empty chart")
                    # Create empty chart with last 6 months labels
                    now = datetime.now()
                    labels = []
                    for i in range(5, -1, -1):
                        date = now - relativedelta(months=i)
                        labels.append(date.strftime("%b %Y"))

                    dashboard_response.invoice_summary_chart = InvoiceSummary(
                        labels=labels,
                        total=[0, 0, 0, 0, 0, 0],
                        lunas=[0, 0, 0, 0, 0, 0],
                        menunggu=[0, 0, 0, 0, 0, 0],
                        kadaluarsa=[0, 0, 0, 0, 0, 0],
                    )

            except Exception as e:
                print(f"❌ Error fetching invoice chart data: {str(e)}")
                import traceback

                traceback.print_exc()
                # Set to null jika ada error
                dashboard_response.invoice_summary_chart = None

        # 7. Widget Status Langganan
        if "view_widget_status_langganan" in user_permissions:
            try:
                status_stmt = (
                    select(Langganan.status, func.count(Langganan.id).label("jumlah"))
                    .group_by(Langganan.status)
                    .order_by(Langganan.status)
                )
                status_results = (await db.execute(status_stmt)).all()
                dashboard_response.status_langganan_chart = ChartData(
                    labels=[row.status for row in status_results],
                    data=[row.jumlah for row in status_results],
                )
            except Exception as e:
                print(f"Error in status_langganan_chart: {e}")

        # 8. Widget Alamat Aktif
        if "view_widget_alamat_aktif" in user_permissions:
            try:
                alamat_stmt = (
                    select(Pelanggan.alamat, func.count(Pelanggan.id).label("jumlah"))
                    .join(Langganan, Pelanggan.id == Langganan.pelanggan_id)
                    .where(Langganan.status == "Aktif")
                    .group_by(Pelanggan.alamat)
                    .order_by(func.count(Pelanggan.id).desc())
                    .limit(20)
                )
                alamat_results = (await db.execute(alamat_stmt)).all()
                if alamat_results:
                    dashboard_response.pelanggan_per_alamat_chart = ChartData(
                        labels=[row.alamat for row in alamat_results],
                        data=[row.jumlah for row in alamat_results],
                    )
            except Exception as e:
                print(f"Error in pelanggan_per_alamat_chart: {e}")

        # PERFORMANCE MONITORING: Log total execution time
        execution_time = time.time() - start_time
        if execution_time > 5.0:  # Log if query takes more than 5 seconds
            print(f"⚠️  Dashboard query took {execution_time:.2f}s - consider optimization")

        return dashboard_response

    except Exception as e:
        # 🛡️ Graceful degradation: Return empty dashboard to avoid 500 errors
        import traceback

        execution_time = time.time() - start_time
        logger.error(f"❌ Dashboard failed after {execution_time:.2f}s: {str(e)}")
        logger.error(f"Dashboard traceback: {traceback.format_exc()}")

        # 🛡️ Return empty dashboard with graceful degradation
        # Create empty data structures with correct types
        empty_revenue_summary = RevenueSummary(total=0.0, periode="bulan", breakdown=[])  # Empty BrandRevenueItem list

        empty_invoice_summary = InvoiceSummary(labels=[], total=[], lunas=[], menunggu=[], kadaluarsa=[])

        empty_chart = ChartData(labels=[], data=[])

        return DashboardData(
            revenue_summary=empty_revenue_summary,
            stat_cards=[],  # Empty stat cards
            lokasi_chart=empty_chart,
            paket_chart=empty_chart,
            growth_chart=empty_chart,
            invoice_summary_chart=empty_invoice_summary,  # Use correct type
            status_langganan_chart=empty_chart,
            pelanggan_per_alamat_chart=empty_chart,
            loyalitas_pembayaran_chart=empty_chart,
        )


class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int


# Tambahkan ini ke file dashboard.py di router dashboard


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
    from datetime import date
    today = date.today()

    # Ambil semua invoice "Belum Dibayar" lalu filter dengan Python logic
    all_unpaid_query = select(Invoice).where(Invoice.status_invoice == "Belum Dibayar")
    all_unpaid_result = await db.execute(all_unpaid_query)
    all_unpaid_invoices = all_unpaid_result.scalars().all()

    # Filter invoice dengan payment link masih aktif
    active_unpaid_count = 0
    expired_count = 0
    for invoice in all_unpaid_invoices:
        try:
            # Logic yang sama dengan Invoice.get_payment_link_status()
            invoice_date = invoice.tgl_invoice
            if isinstance(invoice_date, str):
                invoice_date = date.fromisoformat(invoice_date)
            elif hasattr(invoice_date, 'date'):
                invoice_date = invoice_date.date()

            # Hitung tanggal expiry (tanggal 4 bulan berikutnya)
            if invoice_date.month == 12:
                expiry_date = date(invoice_date.year + 1, 1, 4)
            else:
                expiry_date = date(invoice_date.year, invoice_date.month + 1, 4)

            # Link aktif jika hari ini <= expiry_date
            if today <= expiry_date:
                active_unpaid_count += 1
            else:
                expired_count += 1
                # Debug: log invoice yang expired
                logger.info(f"EXPIRED: {invoice.invoice_number} - Invoice: {invoice_date}, Expiry: {expiry_date}, Today: {today}")
        except Exception as e:
            # Skip jika ada error dalam parsing tanggal
            logger.warning(f"Error processing invoice {invoice.invoice_number}: {e}")
            continue

    logger.info(f"Unpaid invoice stats - Total: {len(all_unpaid_invoices)}, Active: {active_unpaid_count}, Expired: {expired_count}")

    unpaid_count = active_unpaid_count

    stopped_query = select(func.count(Langganan.id)).where(Langganan.status == "Berhenti")
    stopped_result = await db.execute(stopped_query)
    stopped_count = stopped_result.scalar_one_or_none() or 0

    # Generate response dan cache
    response_data = SidebarBadgeResponse(
        suspended_count=suspended_count,
        unpaid_invoice_count=unpaid_count,
        stopped_count=stopped_count,
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
