"""
Langganan Service Layer - Menghilangkan duplikasi business logic dari routers/langganan.py
Mengelola kalkulasi harga, prorate, dan manajemen status langganan.
"""

import json
import logging
import math
from calendar import monthrange
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..models.langganan import Langganan as LanggananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.diskon import Diskon as DiskonModel
from ..models.invoice import Invoice as InvoiceModel
from ..schemas.langganan import LanggananCreate, LanggananUpdate
from ..utils.date_utils import safe_relativedelta_operation

logger = logging.getLogger(__name__)

class LanggananService:
    """
    Service layer untuk manajemen Langganan.
    Logic perhitungan harga (Prorate/Otomatis) dan Pajak dipusatkan di sini.
    """

    @staticmethod
    def calculate_price_and_due_date(
        harga_paket: float,
        pajak_persen: float,
        metode_pembayaran: str,
        start_date: date,
        sertakan_bulan_depan: bool = False
    ) -> Tuple[float, date]:
        """
        Logic perhitungan harga awal dan tanggal jatuh tempo.
        Sesuai dengan logika bisnis asli di routers/langganan.py.
        """
        harga_awal_final = 0.0
        tgl_jatuh_tempo_final = None

        if metode_pembayaran == "Otomatis":
            harga_awal_final = harga_paket * (1 + (pajak_persen / 100))
            tgl_jatuh_tempo_final = (start_date + relativedelta(months=1)).replace(day=1)

        elif metode_pembayaran == "Prorate":
            _, last_day_of_month = monthrange(start_date.year, start_date.month)
            remaining_days = last_day_of_month - start_date.day + 1
            if remaining_days < 0:
                remaining_days = 0

            harga_per_hari = harga_paket / last_day_of_month
            prorated_price_before_tax = harga_per_hari * remaining_days
            harga_prorate_final = prorated_price_before_tax * (1 + (pajak_persen / 100))

            if sertakan_bulan_depan:
                harga_normal_full = harga_paket * (1 + (pajak_persen / 100))
                harga_awal_final = harga_prorate_final + harga_normal_full
            else:
                harga_awal_final = harga_prorate_final

            tgl_jatuh_tempo_final = date(start_date.year, start_date.month, last_day_of_month)

        return round(harga_awal_final, 0), tgl_jatuh_tempo_final

    async def apply_diskon_to_price(self, db: AsyncSession, langganan: LanggananModel) -> float:
        """Apply diskon secara dynamic ke harga langganan (Otomatis)."""
        if not langganan.harga_awal or not langganan.pelanggan:
            return langganan.harga_awal or 0.0

        if langganan.metode_pembayaran == "Prorate":
            return float(langganan.harga_awal)

        tanggal_hari_ini = date.today()
        cluster_to_check = langganan.pelanggan.alamat if langganan.pelanggan.alamat and langganan.pelanggan.alamat.strip() else None

        if not cluster_to_check:
            return langganan.harga_awal

        diskon_query = (
            select(DiskonModel)
            .where(DiskonModel.cluster == cluster_to_check)
            .where(DiskonModel.is_active == True)
            .where((DiskonModel.tgl_mulai.is_(None)) | (DiskonModel.tgl_mulai <= tanggal_hari_ini))
            .where((DiskonModel.tgl_selesai.is_(None)) | (DiskonModel.tgl_selesai >= tanggal_hari_ini))
            .order_by(DiskonModel.persentase_diskon.desc())
        )

        diskon_result = await db.execute(diskon_query)
        diskon_applied = diskon_result.scalar_one_or_none()

        if not diskon_applied:
            return float(langganan.harga_awal)

        diskon_persen = float(diskon_applied.persentase_diskon)
        diskon_amount = math.floor((float(langganan.harga_awal) * diskon_persen / 100) + 0.5)
        return float(langganan.harga_awal) - diskon_amount

    async def create_langganan(self, db: AsyncSession, langganan_data: LanggananCreate) -> LanggananModel:
        """Membuat langganan baru dengan validasi dan kalkulasi otomatis."""
        # 1. Validasi pelanggan
        pelanggan = await db.get(
            PelangganModel,
            langganan_data.pelanggan_id,
            options=[joinedload(PelangganModel.harga_layanan)],
        )
        if not pelanggan or not pelanggan.harga_layanan:
            raise ValueError("Data Brand pelanggan tidak ditemukan.")

        # 2. Validasi data teknis (Wajib ada)
        data_teknis_query = select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == langganan_data.pelanggan_id)
        data_teknis = (await db.execute(data_teknis_query)).scalar_one_or_none()

        if not data_teknis:
            raise ValueError(f"Pelanggan '{pelanggan.nama}' belum memiliki data teknis. NOC harus menambahkannya terlebih dahulu.")

        # 3. Validasi paket
        paket = await db.get(PaketLayananModel, langganan_data.paket_layanan_id)
        if not paket:
            raise ValueError("Paket Layanan tidak ditemukan.")

        # 4. Kalkulasi
        start_date = langganan_data.tgl_mulai_langganan or date.today()
        harga_awal_final, tgl_jatuh_tempo_final = self.calculate_price_and_due_date(
            harga_paket=float(paket.harga),
            pajak_persen=float(pelanggan.harga_layanan.pajak),
            metode_pembayaran=langganan_data.metode_pembayaran,
            start_date=start_date,
            sertakan_bulan_depan=getattr(langganan_data, 'sertakan_bulan_depan', False)
        )

        # 5. Simpan ke database
        db_langganan = LanggananModel(
            pelanggan_id=langganan_data.pelanggan_id,
            paket_layanan_id=langganan_data.paket_layanan_id,
            status=langganan_data.status,
            metode_pembayaran=langganan_data.metode_pembayaran,
            harga_awal=harga_awal_final,
            tgl_jatuh_tempo=tgl_jatuh_tempo_final,
            tgl_mulai_langganan=start_date,
        )

        db.add(db_langganan)
        await db.commit()

        # Load relations for response
        query = (
            select(LanggananModel)
            .where(LanggananModel.id == db_langganan.id)
            .options(
                joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
                joinedload(LanggananModel.paket_layanan),
            )
        )
        return (await db.execute(query)).scalar_one()

    async def update_langganan(self, db: AsyncSession, langganan_id: int, langganan_update: LanggananUpdate) -> LanggananModel:
        """Update data langganan dengan penanganan status 'Berhenti' otomatis."""
        db_langganan = await db.get(LanggananModel, langganan_id)
        if not db_langganan:
            raise ValueError("Langganan tidak ditemukan")

        update_data = langganan_update.model_dump(exclude_unset=True)

        # Logika Bisnis: Penanganan Status Berhenti
        if "status" in update_data and update_data["status"] == "Berhenti":
            hari_ini = date.today()
            update_data["tgl_berhenti"] = hari_ini

            riwayat_list = []
            if db_langganan.riwayat_tgl_berhenti:
                try:
                    riwayat_list = json.loads(db_langganan.riwayat_tgl_berhenti)
                except (json.JSONDecodeError, TypeError): pass

            riwayat_list.append({
                "tanggal": hari_ini.isoformat(),
                "alasan": update_data.get("alasan_berhenti", ""),
                "timestamp": datetime.now().isoformat()
            })
            update_data["riwayat_tgl_berhenti"] = json.dumps(riwayat_list)

        elif "status" in update_data and update_data["status"] != "Berhenti" and db_langganan.status == "Berhenti":
            update_data["tgl_berhenti"] = None

        for key, value in update_data.items():
            setattr(db_langganan, key, value)

        db.add(db_langganan)
        await db.commit()

        # Load relations for response
        query = (
            select(LanggananModel)
            .where(LanggananModel.id == db_langganan.id)
            .options(
                joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
                joinedload(LanggananModel.paket_layanan),
            )
        )
        return (await db.execute(query)).scalar_one()

    async def get_filtered_langganan_stmt(
        self,
        search: Optional[str] = None,
        alamat: Optional[str] = None,
        paket_layanan_name: Optional[str] = None,
        status: Optional[str] = None,
        jatuh_tempo_start: Optional[str] = None,
        jatuh_tempo_end: Optional[str] = None,
        for_invoice_selection: bool = False
    ):
        """Membangun query statement untuk list langganan."""
        query = (
            select(LanggananModel)
            .join(LanggananModel.pelanggan)
            .outerjoin(PelangganModel.data_teknis)
            .options(
                joinedload(LanggananModel.pelanggan).options(
                    joinedload(PelangganModel.harga_layanan),
                    joinedload(PelangganModel.langganan),
                    joinedload(PelangganModel.data_teknis),
                ),
                joinedload(LanggananModel.paket_layanan),
            )
        )

        if for_invoice_selection:
            query = query.where(LanggananModel.status != "Berhenti")

        if search:
            search_term = f"%{search}%"
            query = query.where(or_(
                PelangganModel.nama.ilike(search_term),
                DataTeknisModel.id_pelanggan.ilike(search_term),
                PelangganModel.no_telp.ilike(search_term),
                PelangganModel.email.ilike(search_term),
            ))

        if alamat:
            query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))

        if paket_layanan_name:
            query = query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)

        if status:
            query = query.where(LanggananModel.status == status)

        if jatuh_tempo_start:
            try:
                start_date = datetime.strptime(jatuh_tempo_start, "%Y-%m-%d").date()
                query = query.where(LanggananModel.tgl_jatuh_tempo >= start_date)
            except ValueError: pass

        if jatuh_tempo_end:
            try:
                end_date = datetime.strptime(jatuh_tempo_end, "%Y-%m-%d").date()
                query = query.where(LanggananModel.tgl_jatuh_tempo <= end_date)
            except ValueError: pass

        return query
