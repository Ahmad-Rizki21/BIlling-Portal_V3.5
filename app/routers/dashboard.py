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

    # 1. Widget Pendapatan Bulanan (Tidak ada perubahan)
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
        # Query untuk kartu brand (Tetap sama)
        pelanggan_count_stmt = (
            select(HargaLayanan.brand, func.count(Pelanggan.id))
            .join(Pelanggan, HargaLayanan.id_brand == Pelanggan.id_brand, isouter=True)
            .group_by(HargaLayanan.brand)
        )
        pelanggan_counts = (await db.execute(pelanggan_count_stmt)).all()
        pelanggan_by_brand = {brand.lower(): count for brand, count in pelanggan_counts}

        # --- REVISI: LOGIKA CHART LOYALITAS (PENGGANTI STATCARD) ---
        
        # 1. Subquery A: Daftar ID pelanggan yang punya tagihan TERTUNGGAK
        outstanding_payers_sq = (
            select(Invoice.pelanggan_id)
            .where(Invoice.status_invoice.in_(['Belum Dibayar', 'Kadaluarsa']))
            .distinct()
        )
        
        # 2. Subquery B: Daftar ID pelanggan yang PERNAH telat bayar
        ever_late_payers_sq = (
            select(Invoice.pelanggan_id)
            .where(Invoice.paid_at > Invoice.tgl_jatuh_tempo)
            .distinct()
        )

        # 3. Query utama: Hitung semua pelanggan AKTIF dan bagi jadi 3 grup
        categorization_stmt = (
            select(
                # Grup 1: Menunggak (Punya tagihan tertunggak)
                func.sum(case((Langganan.pelanggan_id.in_(outstanding_payers_sq), 1), else_=0)).label("count_menunggak"),
                
                # Grup 2: Lunas Tapi Telat (TIDAK menunggak, TAPI PERNAH telat)
                func.sum(case((
                    and_(
                        not_(Langganan.pelanggan_id.in_(outstanding_payers_sq)), 
                        Langganan.pelanggan_id.in_(ever_late_payers_sq)
                    ), 1
                ), else_=0)).label("count_lunas_telat"),
                
                # Grup 3: Setia On-Time (TIDAK menunggak DAN TIDAK PERNAH telat)
                func.sum(case((
                    and_(
                        not_(Langganan.pelanggan_id.in_(outstanding_payers_sq)), 
                        not_(Langganan.pelanggan_id.in_(ever_late_payers_sq))
                    ), 1
                ), else_=0)).label("count_setia")
            )
            .select_from(Langganan)
            .where(Langganan.status == 'Aktif')
        )
        
        loyalty_counts = (await db.execute(categorization_stmt)).first()
        
        # 4. Masukkan hasil ke skema ChartData (Asumsi Anda sudah menambahkannya ke schema DashboardData)
        if loyalty_counts:
            dashboard_response.loyalitas_pembayaran_chart = ChartData(
                labels=["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"],
                data=[
                    loyalty_counts.count_setia or 0,
                    loyalty_counts.count_lunas_telat or 0,
                    loyalty_counts.count_menunggak or 0
                ]
            )
        # --- AKHIR REVISI LOGIKA CHART ---

        # REVISI: Hapus StatCard Setia & Telat. Sisakan 3 kartu brand.
        pelanggan_stats = [
            StatCard(title="Jumlah Pelanggan Jakinet", value=pelanggan_by_brand.get("jakinet", 0), description="Total Pelanggan Jakinet"),
            StatCard(title="Jumlah Pelanggan Jelantik", value=pelanggan_by_brand.get("jelantik", 0), description="Total Pelanggan Jelantik"),
            StatCard(title="Pelanggan Jelantik Nagrak", value=pelanggan_by_brand.get("jelantik nagrak", 0), description="Total Pelanggan Rusun Nagrak"),
        ]
        temp_stat_cards.extend(pelanggan_stats)

    # Blok Statistik Server (Tidak ada perubahan, sekarang ditempatkan dengan benar)
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
            .join(Langganan, PaketLayanan.id == Langganan.paket_layanan_id, isouter=True)
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
            labels=[datetime.strptime(item.bulan, "%Y-%m").strftime("%b %Y") for item in growth_data],
            data=[item.jumlah for item in growth_data],
        )

    # 6. Widget Chart Invoice Bulanan (Tidak ada perubahan)
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

    # --- REVISI: PERBAIKAN INDENTASI ---
    # Blok 'if' ini dipindahkan ke level indentasi root (sejajar dengan if lainnya)
    if "view_widget_status_langganan" in user_permissions: 
        status_stmt = select(
            Langganan.status,
            func.count(Langganan.id).label("jumlah")
        ).group_by(Langganan.status).order_by(Langganan.status)

        # REVISI: Dua baris ini sekarang di-indent DENGAN BENAR (di dalam blok if)
        status_results = (await db.execute(status_stmt)).all()
        dashboard_response.status_langganan_chart = ChartData(
            labels=[row.status for row in status_results],
            data=[row.jumlah for row in status_results]
        )

    # --- REVISI: PERBAIKAN INDENTASI ---
    # Blok 'if' ini juga dipindahkan ke level indentasi root
    if "view_widget_alamat_aktif" in user_permissions:
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
    
        # REVISI: Logika ini sekarang di-indent DENGAN BENAR (di dalam blok if)
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

class LoyalitasUserDetail(BaseModel):
    id: Optional[int] = None           
    nama: Optional[str] = None         
    id_pelanggan: Optional[int] = None  # Ubah ke int jika diperlukan
    alamat: Optional[str] = None
    no_telp: Optional[str] = None

# Tambahkan ini ke file dashboard.py di router dashboard

@router.get("/loyalitas-users-by-segment")
async def get_loyalty_users_by_segment(
    segmen: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Mengambil daftar user berdasarkan segmen loyalitas pembayaran dari data REAL
    """
    try:
        from ..models.pelanggan import Pelanggan
        from ..models.langganan import Langganan  
        from ..models.invoice import Invoice
        
        users_list = []
        
        # Query pelanggan aktif dengan relasi lengkap
        pelanggan_query = select(Pelanggan).join(
            Langganan, Pelanggan.id == Langganan.pelanggan_id
        ).where(
            Langganan.status == "Aktif"
        ).options(
            selectinload(Pelanggan.langganan),
            selectinload(Pelanggan.data_teknis)
        ).distinct()
        
        result = await db.execute(pelanggan_query)
        all_active_customers = result.scalars().all()
        
        for pelanggan in all_active_customers:
            # PERBAIKAN: Invoice menggunakan pelanggan_id langsung, bukan langganan_id
            invoice_query = select(Invoice).where(
                Invoice.pelanggan_id == pelanggan.id
            ).order_by(Invoice.tgl_jatuh_tempo.desc())
            
            invoice_result = await db.execute(invoice_query)
            invoices = invoice_result.scalars().all()
            
            if not invoices:
                continue
                
            # Analisis pola pembayaran berdasarkan invoice terbaru dan historis
            recent_invoices = invoices[:5]  # 5 invoice terbaru
            total_lunas = 0
            total_telat = 0
            has_nunggak = False
            
            for invoice in recent_invoices:
                if invoice.status_invoice == "Lunas":
                    total_lunas += 1
                    # Periksa apakah bayar telat
                    if (invoice.paid_at and invoice.tgl_jatuh_tempo and 
                        invoice.paid_at.date() > invoice.tgl_jatuh_tempo):
                        total_telat += 1
                elif invoice.status_invoice in ["Belum Dibayar", "Kadaluarsa"]:
                    has_nunggak = True
            
            # Klasifikasi berdasarkan pola pembayaran
            customer_segment = None
            
            if has_nunggak:
                customer_segment = "Menunggak"
            elif total_telat > 0:
                customer_segment = "Lunas (Tapi Telat)"
            elif total_lunas > 0:
                customer_segment = "Setia On-Time"
            
            # Tambahkan ke list jika sesuai segmen yang diminta
            if customer_segment == segmen:
                # PERBAIKAN: data_teknis adalah objek tunggal, bukan list
                id_pelanggan = pelanggan.data_teknis.id_pelanggan if pelanggan.data_teknis else f"PLG-{pelanggan.id:04d}"
                
                users_list.append({
                    "id": pelanggan.id,
                    "nama": pelanggan.nama,
                    "id_pelanggan": id_pelanggan,
                    "alamat": pelanggan.alamat or 'Alamat tidak tersedia',
                    "no_telp": pelanggan.no_telp or 'Nomor tidak tersedia'
                })
        
        return users_list
        
    except Exception as e:
        import traceback
        print(f"Error in loyalitas users: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Gagal mengambil data user loyalitas: {str(e)}"
        )


# Jika dummy data berfungsi, maka coba versi dengan database sederhana ini:
@router.get("/loyalitas-users-by-segment-real") 
async def get_loyalty_users_by_segment_real(
    segmen: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Versi dengan data real dari database
    """
    try:
        # Import di dalam fungsi untuk menghindari circular import
        from ..models.pelanggan import Pelanggan as PelangganModel
        from ..models.langganan import Langganan as LanggananModel
        
        # Query sederhana untuk mengambil pelanggan aktif
        query = select(PelangganModel).join(
            LanggananModel, PelangganModel.id == LanggananModel.pelanggan_id  
        ).where(
            LanggananModel.status == "Aktif"
        ).limit(10)  # Batasi untuk testing
        
        result = await db.execute(query)
        pelanggan_list = result.scalars().all()
        
        users_list = []
        for pelanggan in pelanggan_list:
            users_list.append({
                "id": pelanggan.id,
                "nama": pelanggan.nama,
                "id_pelanggan": f"PLG-{pelanggan.id:04d}",
                "alamat": getattr(pelanggan, 'alamat', 'Alamat tidak tersedia'),
                "no_telp": getattr(pelanggan, 'no_telp', 'Nomor tidak tersedia')
            })
            
        # Return subset berdasarkan segmen (untuk simulasi)
        if segmen == "Setia On-Time":
            return users_list[:3]  # Return 3 user pertama
        elif segmen == "Lunas (Tapi Telat)":
            return users_list[3:6] if len(users_list) > 3 else []
        elif segmen == "Menunggak":
            return users_list[6:] if len(users_list) > 6 else []
        else:
            return []
            
    except Exception as e:
        import traceback
        print(f"Error in real loyalitas users: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return []


# Juga pastikan untuk memperbaiki chart loyalitas jika ada masalah serupa
@router.get("/loyalitas-pembayaran-chart") 
async def get_loyalitas_pembayaran_chart(db: AsyncSession = Depends(get_db)):
    """
    Mengambil data chart loyalitas pembayaran pelanggan
    """
    try:
        # Hitung pelanggan setia (selalu bayar tepat waktu)
        subquery_setia = select(
            Langganan.id.label('langganan_id')
        ).select_from(
            Langganan
        ).join(
            Invoice, Langganan.id == Invoice.langganan_id
        ).where(
            Langganan.status == "Aktif",
            Invoice.status_pembayaran == "Lunas"
        ).group_by(
            Langganan.id
        ).having(
            func.count(
                case((Invoice.tgl_bayar > Invoice.tgl_jatuh_tempo, 1))
            ) == 0
        ).subquery()
        
        setia_count = await db.execute(
            select(func.count()).select_from(subquery_setia)
        )
        setia_total = setia_count.scalar() or 0
        
        # Hitung pelanggan yang lunas tapi telat
        telat_count = await db.execute(
            select(func.count(Langganan.id.distinct())).select_from(
                Langganan
            ).join(
                Invoice, Langganan.id == Invoice.langganan_id
            ).where(
                Langganan.status == "Aktif",
                Invoice.status_pembayaran == "Lunas",
                Invoice.tgl_bayar > Invoice.tgl_jatuh_tempo
            )
        )
        telat_total = telat_count.scalar() or 0
        
        # Hitung pelanggan menunggak
        nunggak_count = await db.execute(
            select(func.count(Langganan.id.distinct())).select_from(
                Langganan
            ).join(
                Invoice, Langganan.id == Invoice.langganan_id
            ).where(
                Langganan.status == "Aktif",
                Invoice.status_pembayaran.in_(["Menunggu Pembayaran", "Kadaluarsa"])
            )
        )
        nunggak_total = nunggak_count.scalar() or 0
        
        return {
            "labels": ["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"],
            "data": [setia_total, telat_total, nunggak_total]
        }
        
    except Exception as e:
        print(f"Error in loyalitas chart: {e}")
        return {
            "labels": ["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"], 
            "data": [0, 0, 0]
        }
    
# ALTERNATIF QUERY - Jika field id_pelanggan ada di tabel Langganan
@router.get("/loyalitas-users-by-segment-alt", response_model=List[LoyalitasUserDetail])
async def get_loyalty_users_by_segment_alternative(
    segmen: str, 
    db: AsyncSession = Depends(get_db)
):
    """
    Alternatif query jika field id_pelanggan ada di tabel Langganan
    """
    
    outstanding_payers_sq = (
        select(Invoice.pelanggan_id)
        .where(Invoice.status_invoice.in_(['Belum Dibayar', 'Kadaluarsa']))
        .distinct()
    ).correlate(None)

    ever_late_payers_sq = (
        select(Invoice.pelanggan_id)
        .where(
            and_(
                Invoice.paid_at.is_not(None),
                func.date(Invoice.paid_at) > Invoice.tgl_jatuh_tempo
            )
        )
        .distinct()
    ).correlate(None)

    # Query dengan join untuk mendapatkan id_pelanggan dari tabel Langganan
    query = (
        select(
            Pelanggan.id,
            Pelanggan.nama,
            Langganan.id_pelanggan,  # Ambil dari tabel Langganan
            Pelanggan.alamat,
            Pelanggan.no_telp
        )
        .join(Langganan, Pelanggan.id == Langganan.pelanggan_id)
        .where(Langganan.status == 'Aktif')
    )

    # Filter berdasarkan segmen
    if segmen == "Setia On-Time":
        query = query.where(
            and_(
                not_(Pelanggan.id.in_(outstanding_payers_sq)),
                not_(Pelanggan.id.in_(ever_late_payers_sq))
            )
        )
    elif segmen == "Lunas (Tapi Telat)":
        query = query.where(
            and_(
                not_(Pelanggan.id.in_(outstanding_payers_sq)),
                Pelanggan.id.in_(ever_late_payers_sq)
            )
        )
    elif segmen == "Menunggak":
        query = query.where(
            Pelanggan.id.in_(outstanding_payers_sq)
        )
    else:
        return []

    result = await db.execute(query.order_by(Pelanggan.nama))
    return result.all()


# DEBUGGING HELPER - Untuk melihat struktur tabel yang sebenarnya
@router.get("/debug-table-structure")
async def debug_table_structure(db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk debugging - melihat field yang tersedia di tabel
    """
    try:
        # Ambil satu record dari setiap tabel untuk melihat field yang tersedia
        pelanggan_sample = await db.execute(select(Pelanggan).limit(1))
        pelanggan_record = pelanggan_sample.first()
        
        langganan_sample = await db.execute(select(Langganan).limit(1))
        langganan_record = langganan_sample.first()
        
        result = {
            "pelanggan_fields": dir(pelanggan_record[0]) if pelanggan_record else "No records found",
            "langganan_fields": dir(langganan_record[0]) if langganan_record else "No records found"
        }
        
        return result
        
    except Exception as e:
        return {"error": str(e)}


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