from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, or_, and_, not_
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import asyncio
from pydantic import BaseModel
from collections import defaultdict
import locale

# Impor model dengan nama yang akan kita gunakan secara konsisten
from ..models import (
    Invoice,
    Pelanggan,
    HargaLayanan,
    MikrotikServer,
    PaketLayanan,
    Langganan,
)
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


async def _get_revenue_summary(db: AsyncSession) -> RevenueSummary:
    """Helper untuk mengambil ringkasan pendapatan bulanan."""
    now = datetime.now()
    revenue_stmt = (
        select(
            HargaLayanan.brand, func.sum(Invoice.total_harga).label("total_revenue")
        )
        .select_from(Invoice)
        .join(Pelanggan, Invoice.pelanggan_id == Pelanggan.id, isouter=True)
        .join(
            HargaLayanan, Pelanggan.id_brand == HargaLayanan.id_brand, isouter=True
        )
        .where(
            Invoice.status_invoice == "Lunas",
            HargaLayanan.brand.is_not(None),
            func.extract("year", Invoice.paid_at) == now.year,
            func.extract("month", Invoice.paid_at) == now.month,
        )
        .group_by(HargaLayanan.brand)
    )
    revenue_results = (await db.execute(revenue_stmt)).all()
    brand_breakdown = [
        BrandRevenueItem(brand=row.brand, revenue=float(row.total_revenue or 0.0))
        for row in revenue_results
    ]
    total_revenue = sum(item.revenue for item in brand_breakdown)
    next_month_date = now + relativedelta(months=1)
    periode_str = next_month_date.strftime("%B %Y")

    return RevenueSummary(
        total=total_revenue, periode=periode_str, breakdown=brand_breakdown
    )


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
    """Helper untuk mengambil data chart loyalitas pembayaran."""
    outstanding_payers_sq = (
        select(Invoice.pelanggan_id)
        .where(Invoice.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"]))
        .distinct()
    )
    ever_late_payers_sq = (
        select(Invoice.pelanggan_id)
        .where(Invoice.paid_at > Invoice.tgl_jatuh_tempo)
        .distinct()
    )
    categorization_stmt = select(
        func.sum(case((Langganan.pelanggan_id.in_(outstanding_payers_sq), 1), else_=0)).label("count_menunggak"),
        func.sum(case((and_(not_(Langganan.pelanggan_id.in_(outstanding_payers_sq)), Langganan.pelanggan_id.in_(ever_late_payers_sq)), 1), else_=0)).label("count_lunas_telat"),
        func.sum(case((and_(not_(Langganan.pelanggan_id.in_(outstanding_payers_sq)), not_(Langganan.pelanggan_id.in_(ever_late_payers_sq))), 1), else_=0)).label("count_setia"),
    ).select_from(Langganan).where(Langganan.status == "Aktif")

    loyalty_counts = (await db.execute(categorization_stmt)).first()
    if loyalty_counts:
        return ChartData(
            labels=["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"],
            data=[
                loyalty_counts.count_setia or 0,
                loyalty_counts.count_lunas_telat or 0,
                loyalty_counts.count_menunggak or 0,
            ],
        )
    return ChartData(labels=[], data=[])


async def _get_mikrotik_status_counts(db: AsyncSession) -> dict:
    """Helper untuk memeriksa status online/offline semua server Mikrotik secara paralel."""
    all_servers = (await db.execute(select(MikrotikServer))).scalars().all()
    if not all_servers:
        return {"online": 0, "offline": 0, "total": 0}

    async def check_status(server):
        loop = asyncio.get_event_loop()
        api, conn = await loop.run_in_executor(None, mikrotik_service.get_api_connection, server)
        if conn: conn.disconnect()
        return bool(api)

    results = await asyncio.gather(*(check_status(server) for server in all_servers))
    online_count = sum(1 for res in results if res)
    return {"online": online_count, "offline": len(all_servers) - online_count, "total": len(all_servers)}


class MikrotikStatus(BaseModel):
    online: int
    offline: int


@router.get("/", response_model=DashboardData)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
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

    # --- OPTIMISASI: Jalankan semua pengambilan data secara paralel ---
    tasks = {}

    if "view_widget_pendapatan_bulanan" in user_permissions:
        tasks['revenue_summary'] = asyncio.create_task(_get_revenue_summary(db))

    if "view_widget_statistik_pelanggan" in user_permissions:
        tasks['pelanggan_stats'] = asyncio.create_task(_get_pelanggan_stat_cards(db))
        tasks['loyalty_chart'] = asyncio.create_task(_get_loyalty_chart(db))

    if "view_widget_statistik_server" in user_permissions:
        tasks['server_stats'] = asyncio.create_task(_get_mikrotik_status_counts(db))

    # Jalankan semua task yang sudah dikumpulkan
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)
    results_map = dict(zip(tasks.keys(), results))

    # --- Proses hasil dari task yang sudah selesai ---
    if 'revenue_summary' in results_map and not isinstance(results_map['revenue_summary'], Exception):
        dashboard_response.revenue_summary = results_map['revenue_summary']

    temp_stat_cards = []
    if 'pelanggan_stats' in results_map and not isinstance(results_map['pelanggan_stats'], Exception):
        temp_stat_cards.extend(results_map['pelanggan_stats'])

    if 'loyalty_chart' in results_map and not isinstance(results_map['loyalty_chart'], Exception):
        dashboard_response.loyalitas_pembayaran_chart = results_map['loyalty_chart']

    if 'server_stats' in results_map and not isinstance(results_map['server_stats'], Exception):
        server_counts = results_map['server_stats']
        server_stats = [
            StatCard(title="Total Servers", value=server_counts['total'], description="Total Mikrotik servers"),
            StatCard(title="Online Servers", value=server_counts['online'], description="Servers currently online"),
            StatCard(title="Offline Servers", value=server_counts['offline'], description="Servers currently offline"),
        ]
        temp_stat_cards.extend(server_stats)

    if temp_stat_cards:
        dashboard_response.stat_cards = temp_stat_cards

    # 3. Widget Chart Pelanggan per Lokasi (Tidak ada perubahan)
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

    # 4. Widget Chart Pelanggan per Paket (Tidak ada perubahan)
    if "view_widget_pelanggan_per_paket" in user_permissions:
        paket_stmt = (
            select(PaketLayanan.kecepatan, func.count(Langganan.id))
            .join(
                Langganan, PaketLayanan.id == Langganan.paket_layanan_id, isouter=True
            )
            .group_by(PaketLayanan.kecepatan)
            .order_by(PaketLayanan.kecepatan)
        )
        paket_data = (await db.execute(paket_stmt)).all()
        dashboard_response.paket_chart = ChartData(
            labels=[f"{item[0]} Mbps" for item in paket_data],
            data=[item[1] for item in paket_data],
        )

    # 5. Widget Chart Tren Pertumbuhan Pelanggan (Tidak ada perubahan)
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
            labels=[
                datetime.strptime(item.bulan, "%Y-%m").strftime("%b %Y")
                for item in growth_data
            ],
            data=[item.jumlah for item in growth_data],
        )

    # 6. Widget Chart Invoice Bulanan (Tidak ada perubahan)
    if "view_widget_invoice_bulanan" in user_permissions:
        six_months_ago = datetime.now() - timedelta(days=180)
        invoice_stmt = (
            select(
                func.date_format(Invoice.tgl_invoice, "%Y-%m").label("bulan"),
                func.count(Invoice.id).label("total"),
                func.sum(func.if_(Invoice.status_invoice == "Lunas", 1, 0)).label(
                    "lunas"
                ),
                func.sum(
                    func.if_(Invoice.status_invoice == "Belum Dibayar", 1, 0)
                ).label("menunggu"),
                func.sum(func.if_(Invoice.status_invoice == "Kadaluarsa", 1, 0)).label(
                    "kadaluarsa"
                ),
            )
            .where(Invoice.tgl_invoice >= six_months_ago)
            .group_by("bulan")
            .order_by("bulan")
        )
        invoice_data = (await db.execute(invoice_stmt)).all()
        dashboard_response.invoice_summary_chart = InvoiceSummary(
            labels=[
                datetime.strptime(item.bulan, "%Y-%m").strftime("%b")
                for item in invoice_data
            ],
            total=[item.total or 0 for item in invoice_data],
            lunas=[item.lunas or 0 for item in invoice_data],
            menunggu=[item.menunggu or 0 for item in invoice_data],
            kadaluarsa=[item.kadaluarsa or 0 for item in invoice_data],
        )

    # --- REVISI: PERBAIKAN INDENTASI ---
    # Blok 'if' ini dipindahkan ke level indentasi root (sejajar dengan if lainnya)
    if "view_widget_status_langganan" in user_permissions:
        status_stmt = (
            select(Langganan.status, func.count(Langganan.id).label("jumlah"))
            .group_by(Langganan.status)
            .order_by(Langganan.status)
        )

        # REVISI: Dua baris ini sekarang di-indent DENGAN BENAR (di dalam blok if)
        status_results = (await db.execute(status_stmt)).all()
        dashboard_response.status_langganan_chart = ChartData(
            labels=[row.status for row in status_results],
            data=[row.jumlah for row in status_results],
        )

    # --- REVISI: PERBAIKAN INDENTASI ---
    # Blok 'if' ini juga dipindahkan ke level indentasi root
    if "view_widget_alamat_aktif" in user_permissions:
        alamat_stmt = (
            select(Pelanggan.alamat, func.count(Pelanggan.id).label("jumlah"))
            .join(Langganan, Pelanggan.id == Langganan.pelanggan_id)
            .where(Langganan.status == "Aktif")
            .group_by(Pelanggan.alamat)
            .order_by(func.count(Pelanggan.id).desc())
            .limit(7)
        )

        # REVISI: Logika ini sekarang di-indent DENGAN BENAR (di dalam blok if)
        alamat_results = (await db.execute(alamat_stmt)).all()
        if alamat_results:
            dashboard_response.pelanggan_per_alamat_chart = ChartData(
                labels=[row.alamat for row in alamat_results],
                data=[row.jumlah for row in alamat_results],
            )

    return dashboard_response


class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int


# Skema untuk respons data badge
class SidebarBadgeResponse(BaseModel):
    suspended_count: int
    unpaid_invoice_count: int
    stopped_count: int


# Tambahkan ini ke file dashboard.py di router dashboard


@router.get("/loyalitas-users-by-segment")
async def get_loyalty_users_by_segment(segmen: str, db: AsyncSession = Depends(get_db)):
    """
    Mengambil daftar user berdasarkan segmen loyalitas pembayaran secara efisien
    tanpa N+1 query.
    """
    try:
        # 1. Get all active customer IDs
        active_customers_stmt = (
            select(Langganan.pelanggan_id).where(Langganan.status == "Aktif").distinct()
        )
        active_customer_ids = (await db.execute(active_customers_stmt)).scalars().all()
        active_customer_ids_set = set(active_customer_ids)

        # 2. Get IDs of customers with outstanding invoices
        outstanding_payers_stmt = (
            select(Invoice.pelanggan_id)
            .where(Invoice.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"]))
            .distinct()
        )
        outstanding_payer_ids = (
            await db.execute(outstanding_payers_stmt)
        ).scalars().all()
        outstanding_payer_ids_set = set(outstanding_payer_ids)

        # 3. Get IDs of customers who have ever paid late
        ever_late_payers_stmt = (
            select(Invoice.pelanggan_id)
            .where(Invoice.paid_at > Invoice.tgl_jatuh_tempo)
            .distinct()
        )
        ever_late_payer_ids = (await db.execute(ever_late_payers_stmt)).scalars().all()
        ever_late_payer_ids_set = set(ever_late_payer_ids)

        # 4. Categorize based on the requested segment
        target_ids = set()
        if segmen == "Menunggak":
            target_ids = active_customer_ids_set.intersection(outstanding_payer_ids_set)
        elif segmen == "Lunas (Tapi Telat)":
            target_ids = active_customer_ids_set.difference(
                outstanding_payer_ids_set
            ).intersection(ever_late_payer_ids_set)
        elif segmen == "Setia On-Time":
            target_ids = active_customer_ids_set.difference(
                outstanding_payer_ids_set
            ).difference(ever_late_payer_ids_set)
        else:
            return []

        if not target_ids:
            return []

        # 5. Fetch the full details for the target customers
        final_query = (
            select(Pelanggan)
            .where(Pelanggan.id.in_(list(target_ids)))
            .options(selectinload(Pelanggan.data_teknis))
        )
        final_customers = (await db.execute(final_query)).scalars().all()

        # 6. Format the response
        return [
            {
                "id": p.id,
                "nama": p.nama,
                "id_pelanggan": p.data_teknis.id_pelanggan
                if p.data_teknis
                else f"PLG-{p.id:04d}",
                "alamat": p.alamat or "Alamat tidak tersedia",
                "no_telp": p.no_telp or "Nomor tidak tersedia",
            }
            for p in final_customers
        ]
    except Exception as e:
        import traceback

        print(f"Error in loyalitas users: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Gagal mengambil data user loyalitas: {str(e)}"
        )


@router.get("/sidebar-badges", response_model=SidebarBadgeResponse)
async def get_sidebar_badges(db: AsyncSession = Depends(get_db)):
    # PERBAIKAN: Menggunakan nama 'Langganan' dan 'Invoice'
    suspended_query = select(func.count(Langganan.id)).where(
        Langganan.status == "Suspended"
    )
    suspended_result = await db.execute(suspended_query)
    suspended_count = suspended_result.scalar_one_or_none() or 0

    unpaid_query = select(func.count(Invoice.id)).where(
        Invoice.status_invoice == "Belum Dibayar"
    )
    unpaid_result = await db.execute(unpaid_query)
    unpaid_count = unpaid_result.scalar_one_or_none() or 0

    stopped_query = select(func.count(Langganan.id)).where(
        Langganan.status == "Berhenti"
    )
    stopped_result = await db.execute(stopped_query)
    stopped_count = stopped_result.scalar_one_or_none() or 0

    return SidebarBadgeResponse(
        suspended_count=suspended_count,
        unpaid_invoice_count=unpaid_count,
        stopped_count=stopped_count,
    )


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
