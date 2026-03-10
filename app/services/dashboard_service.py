from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, case, or_, and_, desc
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import asyncio
import time
import logging
import locale
from fastapi import HTTPException, status
from pydantic import BaseModel

from ..models import (
    Invoice as InvoiceModel,
    Pelanggan as PelangganModel,
    HargaLayanan as HargaLayananModel,
    MikrotikServer as MikrotikServerModel,
    PaketLayanan as PaketLayananModel,
    Langganan as LanggananModel,
    DataTeknis as DataTeknisModel,
    TroubleTicket as TroubleTicketModel,
)
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from sqlalchemy.orm import selectinload

from ..schemas.dashboard import (
    DashboardData,
    StatCard,
    ChartData,
    InvoiceSummary,
    RevenueSummary,
    BrandRevenueItem,
    PaketDetail,
    BreakdownItem,
)

from . import mikrotik_service
from ..config import settings

logger = logging.getLogger(__name__)

# Set locale for Indonesian month names
try:
    locale.setlocale(locale.LC_TIME, "id_ID.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "Indonesian")
    except locale.Error:
        logger.warning("Locale Bahasa Indonesia tidak ditemukan di sistem.")
        pass

# Cache global state
_mikrotik_cache = {"data": None, "timestamp": 0}
_mikrotik_lock = asyncio.Lock()
_mikrotik_cache_duration = 180

_sidebar_cache = {"data": None, "timestamp": 0}
_sidebar_cache_duration = 60

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_revenue_summary(self) -> RevenueSummary:
        """Mengambil ringkasan pendapatan bulanan."""
        now = datetime.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if now.month == 12:
            end_of_month = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            end_of_month = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)

        revenue_stmt = (
            select(HargaLayananModel.brand, func.sum(InvoiceModel.total_harga).label("total_revenue"))
            .select_from(InvoiceModel)
            .join(PelangganModel, InvoiceModel.pelanggan_id == PelangganModel.id, isouter=True)
            .join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand, isouter=True)
            .where(
                InvoiceModel.status_invoice == "Lunas",
                HargaLayananModel.brand.is_not(None),
                InvoiceModel.paid_at >= start_of_month,
                InvoiceModel.paid_at < end_of_month,
            )
            .group_by(HargaLayananModel.brand)
        )
        
        revenue_results = (await self.db.execute(revenue_stmt)).all()
        brand_breakdown = [BrandRevenueItem(brand=row.brand, revenue=float(row.total_revenue or 0.0)) for row in revenue_results]
        total_revenue = sum(item.revenue for item in brand_breakdown)
        
        next_month_date = now + relativedelta(months=1)
        periode_str = next_month_date.strftime("%B %Y")

        return RevenueSummary(total=total_revenue, periode=periode_str, breakdown=brand_breakdown)

    async def get_pelanggan_stat_cards(self) -> List[StatCard]:
        """Mengambil data kartu statistik pelanggan."""
        pelanggan_count_stmt = (
            select(HargaLayananModel.brand, func.count(PelangganModel.id))
            .join(PelangganModel, HargaLayananModel.id_brand == PelangganModel.id_brand, isouter=True)
            .group_by(HargaLayananModel.brand)
        )
        pelanggan_counts = (await self.db.execute(pelanggan_count_stmt)).all()
        pelanggan_by_brand = {brand.lower(): count for brand, count in pelanggan_counts if brand}

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

    async def get_loyalty_chart(self) -> ChartData:
        """Mengambil data chart loyalitas pembayaran."""
        outstanding_payers_sq = (
            select(InvoiceModel.pelanggan_id).where(InvoiceModel.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"])).distinct()
        )
        ever_late_payers_sq = select(InvoiceModel.pelanggan_id).where(InvoiceModel.paid_at > InvoiceModel.tgl_jatuh_tempo).distinct()

        categorization_stmt = (
            select(func.count(LanggananModel.id).label("total_active"))
            .select_from(LanggananModel)
            .where(LanggananModel.status == "Aktif")
        )

        total_active = (await self.db.execute(categorization_stmt)).scalar() or 0

        outstanding_count_stmt = select(func.count(LanggananModel.id)).where(
            LanggananModel.status == "Aktif", LanggananModel.pelanggan_id.in_(outstanding_payers_sq)
        )

        ever_late_count_stmt = select(func.count(LanggananModel.id)).where(
            LanggananModel.status == "Aktif",
            LanggananModel.pelanggan_id.in_(ever_late_payers_sq),
            ~LanggananModel.pelanggan_id.in_(outstanding_payers_sq),
        )

        outstanding_count = (await self.db.execute(outstanding_count_stmt)).scalar() or 0
        ever_late_count = (await self.db.execute(ever_late_count_stmt)).scalar() or 0
        setia_count = total_active - outstanding_count - ever_late_count

        return ChartData(
            labels=["Setia On-Time", "Lunas (Tapi Telat)", "Menunggak"],
            data=[
                max(0, setia_count),
                max(0, ever_late_count),
                max(0, outstanding_count),
            ],
        )

    async def get_mikrotik_status_counts_cached(self) -> dict:
        """Cached wrapper server Mikrotik status."""
        global _mikrotik_cache
        current_time = time.time()
        
        if _mikrotik_cache["data"]:
            age = current_time - _mikrotik_cache["timestamp"]
            if age < _mikrotik_cache_duration:
                return _mikrotik_cache["data"]
            
            if not _mikrotik_lock.locked():
                 all_servers = (await self.db.execute(select(MikrotikServerModel))).scalars().all()
                 server_list = [{"host_ip": s.host_ip, "port": s.port} for s in all_servers]
                 asyncio.create_task(self._refresh_mikrotik_status_bg(server_list))
                 
            return _mikrotik_cache["data"]

        async with _mikrotik_lock:
            if _mikrotik_cache["data"]:
                return _mikrotik_cache["data"]
                
            all_servers = (await self.db.execute(select(MikrotikServerModel))).scalars().all()
            server_list = [{"host_ip": s.host_ip, "port": s.port} for s in all_servers]
            
            await self._refresh_mikrotik_status_logic(server_list)
            return _mikrotik_cache["data"]

    async def _refresh_mikrotik_status_bg(self, server_list: list):
        async with _mikrotik_lock:
            await self._refresh_mikrotik_status_logic(server_list)

    async def _refresh_mikrotik_status_logic(self, server_list: list):
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

    async def get_lokasi_chart(self) -> ChartData:
        """Mengambil data chart pelanggan per lokasi."""
        lokasi_stmt = (
            select(PelangganModel.alamat, func.count(PelangganModel.id))
            .where(PelangganModel.alamat.isnot(None))
            .group_by(PelangganModel.alamat)
            .order_by(func.count(PelangganModel.id).desc())
            .limit(15)
        )
        lokasi_data = (await self.db.execute(lokasi_stmt)).all()
        return ChartData(
            labels=[item[0] for item in lokasi_data if item[0] is not None],
            data=[item[1] for item in lokasi_data if item[0] is not None],
        )

    async def get_paket_chart(self) -> ChartData:
        """Mengambil data chart pelanggan per paket."""
        paket_stmt = (
            select(PaketLayananModel.kecepatan, func.count(LanggananModel.id))
            .join(LanggananModel, PaketLayananModel.id == LanggananModel.paket_layanan_id, isouter=True)
            .where(LanggananModel.status == "Aktif")
            .group_by(PaketLayananModel.kecepatan)
            .order_by(PaketLayananModel.kecepatan)
            .limit(10)
        )
        paket_data = (await self.db.execute(paket_stmt)).all()
        return ChartData(
            labels=[f"{item[0]} Mbps" for item in paket_data],
            data=[item[1] for item in paket_data],
        )

    async def get_growth_chart(self) -> ChartData:
        """Mengambil data chart tren pertumbuhan pelanggan."""
        two_years_ago = datetime.now() - relativedelta(years=2)
        growth_stmt = (
            select(
                func.year(PelangganModel.tgl_instalasi).label("year"),
                func.month(PelangganModel.tgl_instalasi).label("month"),
                func.count(PelangganModel.id).label("jumlah"),
            )
            .where(PelangganModel.tgl_instalasi >= two_years_ago)
            .group_by(func.year(PelangganModel.tgl_instalasi), func.month(PelangganModel.tgl_instalasi))
            .order_by(func.year(PelangganModel.tgl_instalasi), func.month(PelangganModel.tgl_instalasi))
        )
        growth_data = (await self.db.execute(growth_stmt)).all()
        return ChartData(
            labels=[datetime(item.year, item.month, 1).strftime("%b %Y") for item in growth_data],
            data=[item.jumlah for item in growth_data],
        )

    async def get_invoice_summary_chart(self) -> InvoiceSummary:
        """Mengambil data ringkasan invoice bulanan."""
        six_months_ago = datetime.now() - timedelta(days=180)
        invoice_stmt = (
            select(
                func.year(InvoiceModel.tgl_invoice).label("year"),
                func.month(InvoiceModel.tgl_invoice).label("month"),
                func.count(InvoiceModel.id).label("total"),
                func.sum(case((InvoiceModel.status_invoice == "Lunas", 1), else_=0)).label("lunas"),
                func.sum(case((InvoiceModel.status_invoice == "Belum Dibayar", 1), else_=0)).label("menunggu"),
                func.sum(case((InvoiceModel.status_invoice == "Expired", 1), else_=0)).label("kadaluarsa"),
                func.sum(case((InvoiceModel.invoice_type == "automatic", 1), else_=0)).label("otomatis"),
                func.sum(case((InvoiceModel.invoice_type == "manual", 1), else_=0)).label("manual_invoice"),
                func.sum(case((InvoiceModel.is_reinvoice == True, 1), else_=0)).label("reinvoice"),
            )
            .where(InvoiceModel.tgl_invoice >= six_months_ago)
            .where(InvoiceModel.deleted_at.is_(None))
            .group_by(func.year(InvoiceModel.tgl_invoice), func.month(InvoiceModel.tgl_invoice))
            .order_by(func.year(InvoiceModel.tgl_invoice), func.month(InvoiceModel.tgl_invoice))
        )
        invoice_data = (await self.db.execute(invoice_stmt)).all()

        if not invoice_data:
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

    async def get_status_langganan_chart(self) -> ChartData:
        """Mengambil data status langganan."""
        status_stmt = (
            select(LanggananModel.status, func.count(LanggananModel.id).label("jumlah"))
            .group_by(LanggananModel.status)
            .order_by(LanggananModel.status)
        )
        status_results = (await self.db.execute(status_stmt)).all()
        return ChartData(
            labels=[row.status for row in status_results],
            data=[row.jumlah for row in status_results],
        )

    async def get_pelanggan_per_alamat_chart(self) -> ChartData:
        """Mengambil data pelanggan aktif per alamat."""
        alamat_stmt = (
            select(PelangganModel.alamat, func.count(PelangganModel.id).label("jumlah"))
            .join(LanggananModel, PelangganModel.id == LanggananModel.pelanggan_id)
            .where(LanggananModel.status == "Aktif")
            .group_by(PelangganModel.alamat)
            .order_by(func.count(PelangganModel.id).desc())
            .limit(20)
        )
        alamat_results = (await self.db.execute(alamat_stmt)).all()
        return ChartData(
            labels=[row.alamat for row in alamat_results],
            data=[row.jumlah for row in alamat_results],
        )

    async def get_loyalty_users_by_segment(self, segmen: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mengambil daftar user berdasarkan segmen loyalitas pembayaran."""
        try:
            loyalty_query = select(
                PelangganModel.id,
                PelangganModel.nama,
                PelangganModel.alamat,
                PelangganModel.no_telp,
                DataTeknisModel.id_pelanggan,
                func.sum(
                    case(
                        (InvoiceModel.status_invoice.in_(["Belum Dibayar", "Kadaluarsa"]), 1),
                        else_=0
                    )
                ).label("outstanding_count"),
                func.sum(
                    case(
                        (InvoiceModel.paid_at > InvoiceModel.tgl_jatuh_tempo, 1),
                        else_=0
                    )
                ).label("late_count"),
            ).select_from(
                PelangganModel
            ).join(
                LanggananModel, PelangganModel.id == LanggananModel.pelanggan_id
            ).outerjoin(
                InvoiceModel, PelangganModel.id == InvoiceModel.pelanggan_id
            ).outerjoin(
                DataTeknisModel, PelangganModel.id == DataTeknisModel.pelanggan_id
            ).where(
                LanggananModel.status == "Aktif"
            ).group_by(
                PelangganModel.id, PelangganModel.nama, PelangganModel.alamat, PelangganModel.no_telp, DataTeknisModel.id_pelanggan
            )

            loyalty_result = await self.db.execute(loyalty_query)
            loyalty_data = loyalty_result.all()

            filtered_customers = []
            for row in loyalty_data:
                outstanding_count = row.outstanding_count or 0
                late_count = row.late_count or 0

                is_outstanding = outstanding_count > 0
                is_ever_late = late_count > 0

                if segmen == "Menunggak" and is_outstanding:
                    pass
                elif segmen == "Lunas (Tapi Telat)" and not is_outstanding and is_ever_late:
                    pass
                elif segmen == "Setia On-Time" and not is_outstanding and not is_ever_late:
                    pass
                else:
                    continue

                filtered_customers.append({
                    "id": row.id,
                    "nama": row.nama,
                    "id_pelanggan": (row.id_pelanggan if row.id_pelanggan else f"PLG-{row.id:04d}"),
                    "alamat": row.alamat or "Alamat tidak tersedia",
                    "no_telp": row.no_telp or "Nomor tidak tersedia",
                })
            return filtered_customers
        except Exception as e:
            logger.error(f"Error in loyalty users by segment: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def get_sidebar_badges(self) -> Dict[str, int]:
        """Generate sidebar badge data with caching."""
        global _sidebar_cache
        current_time = time.time()
        
        if (_sidebar_cache["data"] and
            current_time - _sidebar_cache["timestamp"] < _sidebar_cache_duration):
            return _sidebar_cache["data"]

        suspended_query = select(func.count(LanggananModel.id)).where(LanggananModel.status == "Suspended")
        suspended_count = (await self.db.execute(suspended_query)).scalar_one_or_none() or 0

        today = date.today()
        active_unpaid_query = (
            select(func.count(InvoiceModel.id))
            .where(
                InvoiceModel.status_invoice == "Belum Dibayar",
                InvoiceModel.tgl_invoice >= date(
                    today.year if today.month > 1 else today.year - 1,
                    today.month - 1 if today.month > 1 else 12,
                    1
                )
            )
        )
        active_unpaid_count = (await self.db.execute(active_unpaid_query)).scalar_one_or_none() or 0

        stopped_query = select(func.count(LanggananModel.id)).where(LanggananModel.status == "Berhenti")
        stopped_count = (await self.db.execute(stopped_query)).scalar_one_or_none() or 0

        total_invoice_query = select(func.count(InvoiceModel.id)).where(InvoiceModel.deleted_at.is_(None))
        total_invoice_count = (await self.db.execute(total_invoice_query)).scalar_one_or_none() or 0

        open_tickets_query = select(func.count(TroubleTicketModel.id)).where(TroubleTicketModel.status == "Open")
        open_tickets_count = (await self.db.execute(open_tickets_query)).scalar_one_or_none() or 0

        response_dict = {
            "suspended_count": suspended_count,
            "unpaid_invoice_count": active_unpaid_count,
            "stopped_count": stopped_count,
            "total_invoice_count": total_invoice_count,
            "open_tickets_count": open_tickets_count,
        }

        _sidebar_cache["data"] = response_dict
        _sidebar_cache["timestamp"] = current_time
        return response_dict

    async def get_paket_details(self) -> Dict[str, PaketDetail]:
        """Mengambil rincian pelanggan per paket dipecah berdasarkan lokasi dan brand."""
        stmt = (
            select(
                PaketLayananModel.kecepatan,
                PelangganModel.alamat,
                HargaLayananModel.brand,
                func.count(PelangganModel.id).label("jumlah"),
            )
            .select_from(PaketLayananModel)
            .join(LanggananModel, PaketLayananModel.id == LanggananModel.paket_layanan_id)
            .join(PelangganModel, LanggananModel.pelanggan_id == PelangganModel.id)
            .join(HargaLayananModel, PelangganModel.id_brand == HargaLayananModel.id_brand)
            .group_by(PaketLayananModel.kecepatan, PelangganModel.alamat, HargaLayananModel.brand)
            .order_by(PaketLayananModel.kecepatan, func.count(PelangganModel.id).desc())
        )

        result = await self.db.execute(stmt)
        raw_data = result.all()

        paket_details_raw: Dict[str, Dict[str, Any]] = {}

        for kecepatan, alamat, brand, jumlah in raw_data:
            if not alamat or not brand:
                continue

            paket_key = f"{kecepatan} Mbps"

            if paket_key not in paket_details_raw:
                paket_details_raw[paket_key] = {
                    "total_pelanggan": 0,
                    "lokasi": {},
                    "brand": {},
                }

            details = paket_details_raw[paket_key]
            details["total_pelanggan"] += jumlah
            details["lokasi"][alamat] = details["lokasi"].get(alamat, 0) + jumlah
            details["brand"][brand] = details["brand"].get(brand, 0) + jumlah

        final_response = {}
        for paket_key, details in paket_details_raw.items():
            sorted_lokasi = sorted(details.get("lokasi", {}).items(), key=lambda item: item[1], reverse=True)
            sorted_brand = sorted(details.get("brand", {}).items(), key=lambda item: item[1], reverse=True)

            final_response[paket_key] = PaketDetail(
                total_pelanggan=int(details.get("total_pelanggan", 0)),
                breakdown_lokasi=[BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_lokasi],
                breakdown_brand=[BreakdownItem(nama=nama, jumlah=jml) for nama, jml in sorted_brand],
            )

        return final_response

    async def get_invoice_generation_monitor(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Widget dashboard untuk monitoring invoice generation."""
        if target_date:
            target_date_obj = date.fromisoformat(target_date)
        else:
            today = date.today()
            m = today.replace(day=1)
            if m.month == 12:
                m_plus_1 = date(m.year + 1, 1, 1)
            else:
                m_plus_1 = date(m.year, m.month + 1, 1)
            
            gen_date_m_plus_1 = m_plus_1 - timedelta(days=5)
            if today >= gen_date_m_plus_1:
                target_date_obj = m_plus_1
            else:
                target_date_obj = m

        should_have_stmt = (
            select(func.count(LanggananModel.id))
            .where(
                LanggananModel.tgl_jatuh_tempo == target_date_obj,
                LanggananModel.status == "Aktif"
            )
        )
        total_should_have = (await self.db.execute(should_have_stmt)).scalar() or 0

        target_year, target_month = target_date_obj.year, target_date_obj.month
        start_of_month = date(target_year, target_month, 1)
        if target_month == 12:
            end_of_month = date(target_year + 1, 1, 1) - timedelta(days=1)
        else:
            end_of_month = date(target_year, target_month + 1, 1) - timedelta(days=1)

        existing_invoices_stmt = (
            select(func.count(func.distinct(InvoiceModel.pelanggan_id)))
            .where(InvoiceModel.tgl_jatuh_tempo.between(start_of_month, end_of_month))
        )
        total_generated = (await self.db.execute(existing_invoices_stmt)).scalar() or 0

        total_skipped = total_should_have - total_generated
        success_rate = round((total_generated / total_should_have * 100) if total_should_have > 0 else 100, 1)

        now = datetime.now()
        today = now.date()
        generation_date = target_date_obj - timedelta(days=5)
        generation_hour = 13

        if total_skipped == 0:
            status_, status_color, status_icon = "HEALTHY", "success", "✅"
            message = "✅ Semua invoice berhasil di-generate"
        elif today < generation_date or (today == generation_date and now.hour < generation_hour):
            status_, status_color, status_icon = "UPCOMING", "info", "🕒"
            total_generated = 0 
            total_skipped = 0 
            success_rate = 0.0
            
            months = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            gen_month_name = months[generation_date.month - 1]
            gen_date_str = f"{generation_date.day} {gen_month_name} {generation_date.year}"
            message = f"🕒 Menunggu jadwal otomatis hari ini jam {generation_hour}:00 WIB" if today == generation_date else f"🕒 Menunggu jadwal generate otomatis pada {gen_date_str} (H-5)"
        elif total_skipped <= 5:
            status_, status_color, status_icon = "NEEDS_ATTENTION", "warning", "⚠️"
            message = f"⚠️ {total_skipped} pelanggan terlewat"
        else:
            status_, status_color, status_icon = "CRITICAL", "error", "🔴"
            message = f"🔴 {total_skipped} pelanggan terlewat"

        return {
            "target_date": target_date_obj.isoformat(),
            "total_should_have": total_should_have,
            "total_generated": total_generated,
            "total_skipped": total_skipped,
            "success_rate": success_rate,
            "status": status_,
            "status_color": status_color,
            "status_icon": status_icon,
            "message": message,
            "detail_url": f"/invoices/skipped-invoice-generation?target_date={target_date_obj.isoformat()}"
        }

    async def get_future_invoice_projection(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """Mendapatkan proyeksi invoice untuk tanggal di masa depan."""
        today = date.today()

        if target_date:
            target_date_obj = date.fromisoformat(target_date)
        else:
            m = today.replace(day=1)
            if m.month == 12:
                m_plus_1 = date(m.year + 1, 1, 1)
            else:
                m_plus_1 = date(m.year, m.month + 1, 1)
            
            gen_date_m_plus_1 = m_plus_1 - timedelta(days=5)
            if today >= gen_date_m_plus_1:
                if m_plus_1.month == 12:
                    target_date_obj = date(m_plus_1.year + 1, 1, 1)
                else:
                    target_date_obj = date(m_plus_1.year, m_plus_1.month + 1, 1)
            else:
                target_date_obj = m_plus_1

        days_until = (target_date_obj - today).days if target_date_obj > today else 0

        estimated_customers_stmt = (
            select(func.count(LanggananModel.id))
            .where(
                LanggananModel.tgl_jatuh_tempo == target_date_obj,
                LanggananModel.status == "Aktif"
            )
        )
        estimated_customers = (await self.db.execute(estimated_customers_stmt)).scalar() or 0

        total_active_stmt = (
            select(func.count(LanggananModel.id))
            .where(LanggananModel.status == "Aktif")
        )
        total_active = (await self.db.execute(total_active_stmt)).scalar() or 0

        projection_date = target_date_obj - timedelta(days=5)
        now = datetime.now()
        generation_hour = 13

        if today > projection_date or (today == projection_date and now.hour >= generation_hour):
            target_year, target_month = target_date_obj.year, target_date_obj.month
            start_of_month = date(target_year, target_month, 1)
            if target_month == 12:
                end_of_month = date(target_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_of_month = date(target_year, target_month + 1, 1) - timedelta(days=1)

            existing_invoices_stmt = (
                select(func.count(func.distinct(InvoiceModel.pelanggan_id)))
                .where(InvoiceModel.tgl_jatuh_tempo.between(start_of_month, end_of_month))
            )
            total_generated = (await self.db.execute(existing_invoices_stmt)).scalar() or 0
            
            if total_generated > 0:
                if total_generated >= (estimated_customers * 0.9):
                    system_status = "Selesai"
                else:
                    system_status = "Sebagian Selesai"
            else:
                 system_status = "Terlewat"
        elif today == projection_date and now.hour < generation_hour:
            system_status = "Menunggu Jadwal"
        else:
            system_status = "Siap" if days_until > 30 else "Persiapan"

        generation_days_until = (projection_date - today).days if projection_date > today else 0

        return {
            "target_date": target_date_obj.isoformat(),
            "estimated_customers": estimated_customers,
            "total_active_customers": total_active,
            "days_until": days_until,
            "generation_date": projection_date.isoformat(),
            "generation_days_until": generation_days_until,
            "system_status": system_status,
            "is_future": days_until > 0,
            "percentage_of_active": round((estimated_customers / total_active * 100) if total_active > 0 else 0, 1)
        }

    def clear_mikrotik_cache(self):
        global _mikrotik_cache
        _mikrotik_cache = {"data": None, "timestamp": 0}

    def clear_sidebar_cache(self):
        global _sidebar_cache
        _sidebar_cache = {"data": None, "timestamp": 0}
