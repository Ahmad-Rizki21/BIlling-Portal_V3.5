# app/services/invoice_service.py
import logging
import math
import re
from datetime import date, datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.diskon import Diskon as DiskonModel
from ..services.rate_limiter import create_invoice_with_rate_limit, InvoicePriority
from ..utils.phone_utils import normalize_phone_for_xendit

logger = logging.getLogger("app.services.invoice")

class InvoiceService:
    @staticmethod
    def calculate_tax(base_price: float, tax_percent: float) -> int:
        """Menghitung pajak dan melakukan rounding ke bawah (floor)"""
        tax_raw = base_price * (tax_percent / 100)
        return math.floor(tax_raw + 0.5)

    @staticmethod
    def generate_invoice_number(brand: str, customer_name: str, due_date: date, address: str, customer_id: str) -> str:
        """Logika standarisasi nomor invoice"""
        import calendar
        name_clean = re.sub(r'[^a-zA-Z0-9]', '', customer_name).upper()
        addr_clean = re.sub(r'[^a-zA-Z0-9]', '', address or '').upper()
        brand_clean = re.sub(r'[^a-zA-Z0-9]', '', brand).upper()
        
        month_name = calendar.month_name[due_date.month].upper()
        period = f"{month_name}-{due_date.year}"
        
        id_suffix = str(customer_id)[-3:]
        return f"{brand_clean}/ftth/{name_clean}/{period}/{addr_clean}/{id_suffix}"

    async def get_active_discount(self, db: AsyncSession, cluster: str) -> Optional[DiskonModel]:
        """Mencari diskon aktif untuk suatu wilayah/cluster"""
        if not cluster: return None
        
        today = date.today()
        stmt = (
            select(DiskonModel)
            .where(DiskonModel.cluster == cluster)
            .where(DiskonModel.is_active == True)
            .where((DiskonModel.tgl_mulai.is_(None)) | (DiskonModel.tgl_mulai <= today))
            .where((DiskonModel.tgl_selesai.is_(None)) | (DiskonModel.tgl_selesai >= today))
            .order_by(DiskonModel.persentase_diskon.desc())
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_filtered_invoices_stmt(
        self, 
        search: Optional[str] = None,
        status_invoice: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        show_active_only: bool = False
    ):
        """Membangun statement query invoice dengan berbagai filter"""
        from sqlalchemy import or_
        
        stmt = select(InvoiceModel).options(
            selectinload(InvoiceModel.pelanggan).selectinload(PelangganModel.data_teknis),
            selectinload(InvoiceModel.pelanggan).selectinload(PelangganModel.harga_layanan),
            selectinload(InvoiceModel.pelanggan).selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan)
        ).order_by(InvoiceModel.created_at.desc())

        if search:
            stmt = stmt.join(InvoiceModel.pelanggan).where(
                or_(
                    InvoiceModel.invoice_number.ilike(f"%{search}%"),
                    InvoiceModel.id_pelanggan.ilike(f"%{search}%"),
                    PelangganModel.nama.ilike(f"%{search}%"),
                    PelangganModel.no_telp.ilike(f"%{search}%")
                )
            )

        if status_invoice:
            stmt = stmt.where(InvoiceModel.status_invoice == status_invoice)

        if start_date:
            stmt = stmt.where(InvoiceModel.tgl_invoice >= start_date)
        
        if end_date:
            stmt = stmt.where(InvoiceModel.tgl_invoice <= end_date)

        if show_active_only:
            stmt = stmt.where(InvoiceModel.status_invoice.in_(["Belum Dibayar", "Expired"]))
        
        return stmt

    async def create_invoice(self, db: AsyncSession, langganan_id: int, is_reinvoice: bool = False, original_invoice_id: Optional[int] = None, reinvoice_reason: Optional[str] = None) -> InvoiceModel:
        """
        Logika terpusat untuk pembuatan invoice baik manual maupun otomatis.
        Terintegrasi dengan Xendit dan sistem diskon.
        """
        # 1. Fetch data dan validasi
        stmt = (
            select(LanggananModel)
            .where(LanggananModel.id == langganan_id)
            .options(
                selectinload(LanggananModel.pelanggan).options(
                    selectinload(PelangganModel.harga_layanan),
                    selectinload(PelangganModel.data_teknis),
                ),
                selectinload(LanggananModel.paket_layanan),
            )
        )
        result = await db.execute(stmt)
        langganan = result.unique().scalar_one_or_none()

        if not langganan:
            raise ValueError(f"Langganan ID {langganan_id} tidak ditemukan")

        pelanggan = langganan.pelanggan
        paket = langganan.paket_layanan
        brand = pelanggan.harga_layanan
        data_teknis = pelanggan.data_teknis

        if not all([pelanggan, paket, brand, data_teknis]):
            raise ValueError(f"Data pendukung tidak lengkap untuk langganan ID {langganan_id}")

        # 2. Perhitungan Tanggal
        actual_due_date = langganan.tgl_jatuh_tempo
        if langganan.metode_pembayaran == "Prorate" and actual_due_date.day == 1:
            actual_due_date = actual_due_date - timedelta(days=1)

        # 3. Cek Duplikat
        if not is_reinvoice:
            existing_stmt = select(InvoiceModel.id).where(
                InvoiceModel.pelanggan_id == langganan.pelanggan_id,
                InvoiceModel.tgl_jatuh_tempo == actual_due_date,
            )
            if (await db.execute(existing_stmt)).scalar_one_or_none():
                 raise ValueError("Invoice untuk periode ini sudah ada.")

        # 4. Generate Nomor Invoice (Sanitized)
        nomor_invoice = self.generate_invoice_number(
            brand.brand, pelanggan.nama, langganan.tgl_jatuh_tempo, pelanggan.alamat, data_teknis.id_pelanggan or "TMP"
        )
        
        # Cek keunikan nomor
        existing_num = (await db.execute(select(InvoiceModel.id).where(InvoiceModel.invoice_number == nomor_invoice))).scalar_one_or_none()
        if existing_num:
            import time
            nomor_invoice = f"{nomor_invoice}/{str(int(time.time()))[-4:]}"

        # 5. Perhitungan Harga & Pajak
        total_harga_awal = float(langganan.harga_awal or 0)
        pajak_persen = float(brand.pajak or 0)
        
        # Hitung mundur pajak ( floor behavior consistent with existing logic)
        harga_dasar = total_harga_awal / (1 + (pajak_persen / 100))
        pajak = round(total_harga_awal - harga_dasar)
        total_harga = total_harga_awal
        total_harga_sebelum_diskon = total_harga

        # 6. Diskon Pelanggan
        diskon_id = None
        diskon_persen = None
        diskon_amount = None
        
        if langganan.metode_pembayaran != "Prorate":
            diskon_applied = await self.get_active_discount(db, pelanggan.alamat)
            if diskon_applied:
                diskon_id = diskon_applied.id
                diskon_persen = float(diskon_applied.persentase_diskon)
                diskon_amount = math.floor((total_harga_sebelum_diskon * diskon_persen / 100) + 0.5)
                total_harga = total_harga_sebelum_diskon - diskon_amount

        # 7. Simpan ke Database
        new_invoice = InvoiceModel(
            invoice_number=nomor_invoice,
            pelanggan_id=pelanggan.id,
            id_pelanggan=data_teknis.id_pelanggan,
            brand=brand.brand,
            total_harga=total_harga,
            no_telp=pelanggan.no_telp,
            email=pelanggan.email,
            tgl_invoice=date.today(),
            tgl_jatuh_tempo=actual_due_date,
            status_invoice="Belum Dibayar",
            invoice_type="reinvoice" if is_reinvoice else ("manual" if original_invoice_id else "automatic"),
            is_reinvoice=is_reinvoice,
            original_invoice_id=original_invoice_id,
            reinvoice_reason=reinvoice_reason,
            diskon_id=diskon_id,
            diskon_persen=diskon_persen,
            diskon_amount=diskon_amount,
            harga_sebelum_diskon=total_harga_sebelum_diskon if diskon_id else None,
        )
        db.add(new_invoice)
        await db.flush()

        # 8. Deskripsi Xendit (Logic Ported)
        from .invoice_description_service import get_invoice_description # Kita buat helper ini nanti
        desc = get_invoice_description(langganan, paket, new_invoice, brand)

        # 9. Create Xendit Payment Link
        priority = InvoicePriority.HIGH if getattr(pelanggan, 'is_vip', False) else InvoicePriority.NORMAL
        x_resp = await create_invoice_with_rate_limit(
            invoice=new_invoice,
            pelanggan=pelanggan,
            paket=paket,
            deskripsi_xendit=desc,
            pajak=pajak,
            no_telp_xendit=normalize_phone_for_xendit(pelanggan.no_telp),
            priority=priority
        )

        new_invoice.payment_link = x_resp.get("short_url") or x_resp.get("invoice_url")
        new_invoice.xendit_id = x_resp.get("id")
        new_invoice.xendit_external_id = x_resp.get("external_id")
        
        await db.commit()
        
        # Load relations for response
        result = await db.execute(
            select(InvoiceModel).where(InvoiceModel.id == new_invoice.id).options(
                selectinload(InvoiceModel.pelanggan).options(
                    selectinload(PelangganModel.harga_layanan),
                    selectinload(PelangganModel.data_teknis),
                    selectinload(PelangganModel.langganan).selectinload(LanggananModel.paket_layanan)
            )
        )
        )
        return result.unique().scalar_one()

    async def process_payment(self, db: AsyncSession, invoice: InvoiceModel, payload: Optional[dict] = None) -> bool:
        """
        Logika terpusat untuk memproses pembayaran lunas.
        Menghitung jatuh tempo berikutnya dan mengaktifkan layanan di Mikrotik.
        """
        from ..models.user import User as UserModel
        from ..models.role import Role as RoleModel
        from ..utils.date_utils import parse_xendit_datetime, safe_to_datetime
        from ..services import mikrotik_service
        from datetime import timezone
        from sqlalchemy import func
        from ..websocket_manager import manager
        from dateutil.relativedelta import relativedelta

        pelanggan = invoice.pelanggan
        if not pelanggan or not pelanggan.langganan:
            logger.error(f"Pelanggan atau langganan tidak ditemukan untuk invoice {invoice.invoice_number}")
            return False

        langganan = pelanggan.langganan[0]
        is_suspended = langganan.status == "Suspended" or not langganan.status

        # 1. Update Invoice status
        invoice.status_invoice = "Lunas"
        if payload:
            invoice.paid_amount = float(payload.get("paid_amount", invoice.total_harga or 0))
            paid_at_str = payload.get("paid_at")
            invoice.paid_at = parse_xendit_datetime(paid_at_str) if paid_at_str else datetime.now(timezone.utc)
        else:
            invoice.paid_amount = invoice.total_harga
            invoice.paid_at = datetime.now(timezone.utc)
        db.add(invoice)

        # 2. Hitung Jatuh Tempo Berikutnya
        next_due_date = None
        current_due_date = invoice.tgl_jatuh_tempo or date.today()
        current_due_dt = safe_to_datetime(current_due_date)

        if langganan.metode_pembayaran == "Prorate":
            paket = langganan.paket_layanan
            brand = pelanggan.harga_layanan
            langganan.metode_pembayaran = "Otomatis"
            
            if not paket or not brand:
                next_due_date = (current_due_dt + relativedelta(months=1)).date().replace(day=1)
            else:
                harga_normal = float(paket.harga) * (1 + (float(brand.pajak) / 100))
                # Tagihan Gabungan (Combined)
                if float(invoice.total_harga or 0) > (harga_normal + 1):
                    months_to_add = 1 if current_due_dt.day == 1 else 2
                    next_due_date = (current_due_dt + relativedelta(months=months_to_add)).date().replace(day=1)
                else:
                    # Prorate Biasa
                    if current_due_dt.day == 1:
                        next_due_date = current_due_dt.date()
                    else:
                        next_due_date = (current_due_dt + relativedelta(months=1)).date().replace(day=1)
                langganan.harga_awal = round(harga_normal, 0)
        else:
            # Pembayaran Normal (Otomatis/Monthly)
            next_due_date = (current_due_dt + relativedelta(months=1)).date().replace(day=1)

        # 3. Update Status Langganan
        langganan.status = "Aktif"
        langganan.tgl_jatuh_tempo = next_due_date
        langganan.tgl_invoice_terakhir = date.today()
        db.add(langganan)

        # 4. Trigger Mikrotik (jika sebelumnya isolir)
        if is_suspended:
            data_teknis = pelanggan.data_teknis
            if data_teknis:
                try:
                    await mikrotik_service.trigger_mikrotik_update(db, langganan, data_teknis, data_teknis.id_pelanggan)
                    data_teknis.mikrotik_sync_pending = False
                    db.add(data_teknis)
                except Exception as e:
                    logger.error(f"Mikrotik activation failed: {e}")
                    data_teknis.mikrotik_sync_pending = True
                    db.add(data_teknis)

        # 5. Notifikasi Real-time
        try:
            target_roles = ["Admin", "NOC", "Finance"]
            u_stmt = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name).in_([r.lower() for r in target_roles]))
            target_ids = (await db.execute(u_stmt)).scalars().all()
            
            if target_ids:
                notif = {
                    "type": "new_payment",
                    "message": f"Pembayaran untuk invoice {invoice.invoice_number} dari {pelanggan.nama} telah diterima.",
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "invoice_id": invoice.id,
                        "invoice_number": invoice.invoice_number,
                        "pelanggan_nama": pelanggan.nama,
                        "amount": float(invoice.total_harga or 0),
                        "payment_method": invoice.metode_pembayaran or "Unknown"
                    }
                }
                await manager.broadcast_to_roles(notif, list(target_ids))
        except Exception as e:
            logger.error(f"Notification error: {e}")

        return True
