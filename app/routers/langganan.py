import csv
import io
import json
import logging
from calendar import monthrange
from datetime import date, datetime
from typing import List, Optional

import chardet
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.diskon import Diskon as DiskonModel
from ..models.user import User as UserModel
from ..auth import get_current_active_user
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..schemas.langganan import (
    Langganan as LanggananSchema,
    LanggananCreate,
    LanggananImport,
    LanggananUpdate,
)
from ..schemas.pelanggan import Pelanggan as PelangganSchema
from ..utils.export import create_langganan_export_response, create_langganan_multi_sheet_export_response

router = APIRouter(prefix="/langganan", tags=["Langganan"])

logger = logging.getLogger(__name__)


# --- Helper Functions ---
import math
from datetime import date as date_class

def format_phone_number(phone_number: str) -> str:
    """
    Format phone number to international format (62 prefix).
    Mendukung semua format input: 08xx, 62xx, +62xx, 8xx.
    """
    from ..utils.phone_utils import normalize_phone_display
    return normalize_phone_display(phone_number)


async def apply_diskon_to_langganan_price(langganan: LanggananModel, db: AsyncSession) -> float:
    """
    Apply diskon secara dynamic ke harga langganan.
    Jika ada diskon aktif untuk cluster pelanggan, harga diskon dikembalikan.
    Jika tidak ada diskon, harga normal dikembalikan.

    CATATAN: User dengan metode pembayaran Prorate TIDAK mendapatkan diskon.
    """
    if not langganan.harga_awal or not langganan.pelanggan:
        return langganan.harga_awal or 0.0

    # Prorate users TIDAK mendapatkan diskon
    if langganan.metode_pembayaran == "Prorate":
        return float(langganan.harga_awal)

    # Cek diskon aktif untuk cluster pelanggan
    tanggal_hari_ini = date_class.today()

    # Gunakan alamat sebagai cluster
    cluster_to_check = langganan.pelanggan.alamat if langganan.pelanggan.alamat and langganan.pelanggan.alamat.strip() else None

    if not cluster_to_check:
        return langganan.harga_awal

    # Cari diskon aktif untuk cluster ini
    diskon_query = (
        select(DiskonModel)
        .where(DiskonModel.cluster == cluster_to_check)
        .where(DiskonModel.is_active == True)
        .where(
            (DiskonModel.tgl_mulai.is_(None)) | (DiskonModel.tgl_mulai <= tanggal_hari_ini)
        )
        .where(
            (DiskonModel.tgl_selesai.is_(None)) | (DiskonModel.tgl_selesai >= tanggal_hari_ini)
        )
        .order_by(DiskonModel.persentase_diskon.desc())
    )

    diskon_result = await db.execute(diskon_query)
    diskon_applied = diskon_result.scalar_one_or_none()

    return calculate_final_price_with_diskon(float(langganan.harga_awal), diskon_applied)


def calculate_final_price_with_diskon(harga_asli: float, diskon_applied: Optional[DiskonModel]) -> float:
    """Helper function untuk menghitung harga setelah diskon (logic dipisah agar bisa re-use)"""
    if not diskon_applied:
        return harga_asli

    diskon_persen = float(diskon_applied.persentase_diskon)
    diskon_amount = math.floor((harga_asli * diskon_persen / 100) + 0.5)
    return harga_asli - diskon_amount


# --- Skema Respons Baru ---
class LanggananListResponse(BaseModel):
    data: List[LanggananSchema]
    total_count: int


# --- Endpoint Utama untuk Manajemen Langganan ---


# POST /langganan - Buat langganan baru
# Endpoint buat nambahin langganan pelanggan ke sistem
# Request body: data langganan (pelanggan_id, paket_layanan_id, status, metode_pembayaran, dll)
# Response: data langganan yang baru dibuat dengan harga yang udah dihitung otomatis
# Fitur:
# - Hitung harga otomatis (include pajak)
# - Dukung metode pembayaran: Otomatis dan Prorate
# - Prorate: hitung harga proporsional bulan ini +/- bulan depan
# - Auto set tanggal jatuh tempo
# Validation: cek pelanggan dan paket layanan harus ada
@router.post("/", response_model=LanggananSchema, status_code=status.HTTP_201_CREATED)
async def create_langganan(
    langganan_data: LanggananCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Membuat langganan baru dengan perhitungan harga otomatis di backend.
    Mendukung metode pembayaran 'Otomatis' dan 'Prorate' (biasa atau gabungan).

    VALIDATION PENTING: Langganan hanya bisa dibuat jika pelanggan sudah memiliki data teknis.
    NOC harus menambahkan data teknis terlebih dahulu sebelum Finance bisa membuat langganan.
    """
    # 1. Validasi pelanggan ada
    pelanggan = await db.get(
        PelangganModel,
        langganan_data.pelanggan_id,
        options=[joinedload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(status_code=404, detail="Data Brand pelanggan tidak ditemukan.")

    # 2. VALIDASI UTAMA: Cek apakah pelanggan sudah punya data teknis
    data_teknis_query = select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == langganan_data.pelanggan_id)
    data_teknis_result = await db.execute(data_teknis_query)
    data_teknis = data_teknis_result.scalar_one_or_none()

    if not data_teknis:
        logger.warning(f"PERCOBAAN LANGGANAN TANPA DATA TEKNIS: Finance mencoba membuat langganan untuk pelanggan ID {langganan_data.pelanggan_id} ({pelanggan.nama}) tanpa data teknis")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Langganan tidak dapat dibuat. Pelanggan '{pelanggan.nama}' belum memiliki data teknis. "
                   f"Tim NOC harus menambahkan data teknis terlebih dahulu sebelum membuat langganan."
        )

    # 3. Validasi paket layanan ada
    paket = await db.get(PaketLayananModel, langganan_data.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan.")

    start_date = langganan_data.tgl_mulai_langganan or date.today()

    harga_paket = float(paket.harga)
    pajak_persen = float(pelanggan.harga_layanan.pajak)
    harga_awal_final = 0.0
    tgl_jatuh_tempo_final = None

    if langganan_data.metode_pembayaran == "Otomatis":
        harga_awal_final = harga_paket * (1 + (pajak_persen / 100))
        tgl_jatuh_tempo_final = (start_date + relativedelta(months=1)).replace(day=1)

    elif langganan_data.metode_pembayaran == "Prorate":
        _, last_day_of_month = monthrange(start_date.year, start_date.month)
        remaining_days = last_day_of_month - start_date.day + 1
        if remaining_days < 0:
            remaining_days = 0

        harga_per_hari = harga_paket / last_day_of_month
        prorated_price_before_tax = harga_per_hari * remaining_days
        harga_prorate_final = prorated_price_before_tax * (1 + (pajak_persen / 100))

        if langganan_data.sertakan_bulan_depan:
            harga_normal_full = harga_paket * (1 + (pajak_persen / 100))
            harga_awal_final = harga_prorate_final + harga_normal_full
        else:
            harga_awal_final = harga_prorate_final

        tgl_jatuh_tempo_final = date(start_date.year, start_date.month, last_day_of_month)

    db_langganan = LanggananModel(
        pelanggan_id=langganan_data.pelanggan_id,
        paket_layanan_id=langganan_data.paket_layanan_id,
        status=langganan_data.status,
        metode_pembayaran=langganan_data.metode_pembayaran,
        harga_awal=round(harga_awal_final, 0),
        tgl_jatuh_tempo=tgl_jatuh_tempo_final,
        tgl_mulai_langganan=start_date,
    )

    db.add(db_langganan)
    await db.commit()

    logger.info(f"LANGGANAN BERHASIL DIBUAT: Finance berhasil membuat langganan untuk pelanggan '{pelanggan.nama}' (ID: {pelanggan.id}) dengan paket '{paket.nama_paket}'")

    query = (
        select(LanggananModel)
        .where(LanggananModel.id == db_langganan.id)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    created_langganan = result.scalar_one()

    return created_langganan


# GET /langganan - Ambil semua data langganan
# Buat nampilin list langganan dengan fitur filter dan pencarian
# Query parameters:
# - search: cari berdasarkan nama pelanggan
# - alamat: filter berdasarkan alamat pelanggan
# - paket_layanan_name: filter berdasarkan nama paket
# - status: filter berdasarkan status (Aktif/Berhenti)
# - brand: filter berdasarkan brand (JAKINET, JELANTIK, JELANTIK Nagrak, dll)
# - jatuh_tempo_start: filter tanggal jatuh tempo mulai
# - jatuh_tempo_end: filter tanggal jatuh tempo akhir
# - for_invoice_selection: kalo true, exclude langganan status "Berhenti"
# - skip: offset pagination (default: 0)
# - limit: jumlah data per halaman (default: 15)
# Response: list langganan dengan total count + eager loading relasi
# Performance: eager loading biar ga N+1 query
@router.get("/", response_model=LanggananListResponse)
async def get_all_langganan(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_name: Optional[str] = None,
    status: Optional[str] = None,
    jatuh_tempo_start: Optional[str] = None,
    jatuh_tempo_end: Optional[str] = None,
    for_invoice_selection: bool = False,
    skip: int = 0,
    limit: Optional[int] = 15,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil semua langganan dengan opsi filter dan paginasi serta total count."""
    base_query = (
        select(LanggananModel)
        .join(LanggananModel.pelanggan)
        .outerjoin(PelangganModel.data_teknis)
        .options(
            joinedload(LanggananModel.pelanggan).options(
                joinedload(PelangganModel.langganan),
                joinedload(PelangganModel.harga_layanan),
                joinedload(PelangganModel.data_teknis),
            ),
            joinedload(LanggananModel.paket_layanan),
        )
    )
    count_query = select(func.count(LanggananModel.id)).join(LanggananModel.pelanggan).outerjoin(PelangganModel.data_teknis)

    if for_invoice_selection:
        base_query = base_query.where(LanggananModel.status != "Berhenti")
        count_query = count_query.where(LanggananModel.status != "Berhenti")

    if search:
        search_term = f"%{search}%"
        filter_condition = or_(
            PelangganModel.nama.ilike(search_term),
            DataTeknisModel.id_pelanggan.ilike(search_term),
            PelangganModel.no_telp.ilike(search_term),
            PelangganModel.email.ilike(search_term),
        )
        base_query = base_query.where(filter_condition)
        count_query = count_query.where(filter_condition)
    if alamat:
        filter_condition = PelangganModel.alamat.ilike(f"%{alamat}%")
        base_query = base_query.where(filter_condition)
        count_query = count_query.where(filter_condition)
    if paket_layanan_name:
        join_condition = base_query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)
        base_query = join_condition
        count_query = count_query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)
    if status:
        filter_condition = LanggananModel.status == status
        base_query = base_query.where(filter_condition)
        count_query = count_query.where(filter_condition)

    
    
    # Filter berdasarkan tanggal jatuh tempo
    if jatuh_tempo_start:
        try:
            start_date = datetime.strptime(jatuh_tempo_start, "%Y-%m-%d").date()
            filter_condition = LanggananModel.tgl_jatuh_tempo >= start_date
            base_query = base_query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    if jatuh_tempo_end:
        try:
            end_date = datetime.strptime(jatuh_tempo_end, "%Y-%m-%d").date()
            filter_condition = LanggananModel.tgl_jatuh_tempo <= end_date
            base_query = base_query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    # --- OPTIMASI PERFORMANCE: Batasi limit jika terlalu besar (maksimal 5000) ---
    if limit is not None:
        limit = min(limit, 5000)
    else:
        limit = 15 # Default limit jika None

    # Get total count before applying pagination
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar_one()

    # Apply ordering and pagination to the main query
    data_query = base_query.order_by(LanggananModel.id.desc())
    if limit is not None:
        data_query = data_query.offset(skip).limit(limit)

    result = await db.execute(data_query)
    langganan_list = result.unique().scalars().all()

    if for_invoice_selection and langganan_list:
        pelanggan_ids = {l.pelanggan_id for l in langganan_list}
        invoice_counts_stmt = (
            select(InvoiceModel.pelanggan_id, func.count(InvoiceModel.id).label("count"))
            .where(InvoiceModel.pelanggan_id.in_(pelanggan_ids))
            .group_by(InvoiceModel.pelanggan_id)
        )
        invoice_counts_result = await db.execute(invoice_counts_stmt)
        invoice_counts_map = {pid: count for pid, count in invoice_counts_result}

        for langganan in langganan_list:
            pelanggan = langganan.pelanggan
            is_new_user = False

            if pelanggan and len(pelanggan.langganan) == 1:
                if invoice_counts_map.get(pelanggan.id, 0) == 0:
                    is_new_user = True

            langganan.is_new_user = is_new_user

    # --- OPTIMASI PERFORMANCE (N+1 Query Prevention): Fetch all active discounts once ---
    tanggal_hari_ini = date_class.today()
    diskon_query = (
        select(DiskonModel)
        .where(DiskonModel.is_active == True)
        .where((DiskonModel.tgl_mulai.is_(None)) | (DiskonModel.tgl_mulai <= tanggal_hari_ini))
        .where((DiskonModel.tgl_selesai.is_(None)) | (DiskonModel.tgl_selesai >= tanggal_hari_ini))
        .order_by(DiskonModel.persentase_diskon.desc())
    )
    all_discounts_result = await db.execute(diskon_query)
    all_active_discounts = all_discounts_result.scalars().all()
    
    # Create mapping cluster -> diskon (ambil yang persentasenya paling besar per cluster)
    discount_map = {}
    for d in all_active_discounts:
        if d.cluster not in discount_map:
            discount_map[d.cluster] = d

    langganan_response_data = []
    for langganan in langganan_list:
        harga_asli = float(langganan.harga_awal) if langganan.harga_awal else 0.0
        
        # Logika bisnis: Prorate tidak dapat diskon
        if langganan.metode_pembayaran == "Prorate":
            harga_with_diskon = harga_asli
        else:
            cluster = langganan.pelanggan.alamat if langganan.pelanggan and langganan.pelanggan.alamat else None
            diskon_applied = discount_map.get(cluster) if cluster else None
            harga_with_diskon = calculate_final_price_with_diskon(harga_asli, diskon_applied)

        # FIX: Pastikan relasi 'pelanggan' dan 'paket_layanan' ikut terbawa
        # Gunakan schema model_validate untuk menangani objek SQLAlchemy dengan benar
        langganan_schema = LanggananSchema.model_validate(langganan)
        langganan_dict = langganan_schema.model_dump()
        
        # Override harga dengan harga yang sudah diproses diskon
        langganan_dict['harga_awal'] = harga_with_diskon
        
        # Sertakan status is_new_user jika dihitung
        if hasattr(langganan, 'is_new_user'):
            langganan_dict['is_new_user'] = langganan.is_new_user
            
        langganan_response_data.append(langganan_dict)

    return LanggananListResponse(data=langganan_response_data, total_count=total_count)

    return LanggananListResponse(data=langganan_response_data, total_count=total_count)


# GET /langganan/export - Export data langganan ke CSV atau Excel
# Buat export data langganan ke file dengan format yang dipilih (CSV/Excel) dengan filter yang sama seperti list
# Query parameters:
# - search: filter pencarian (sama seperti di list)
# - alamat: filter berdasarkan alamat
# - paket_layanan_name: filter berdasarkan nama paket
# - status: filter berdasarkan status
# - brand: filter berdasarkan brand (JAKINET, JELANTIK, JELANTIK Nagrak, dll)
# - jatuh_tempo_start: filter tanggal jatuh tempo mulai
# - jatuh_tempo_end: filter tanggal jatuh tempo akhir
# - format: format export (csv atau excel), default csv
# Response: file export dengan kolom: Nama Pelanggan, Email, Nomor Telepon, Brand, Paket Layanan, Status, Metode Pembayaran, Harga, dll
# Format file: CSV dengan BOM atau Excel dengan formatting, timestamp di filename
# Performance: eager loading biar efficient
@router.get("/export", response_class=StreamingResponse)
async def export_langganan(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_name: Optional[str] = None,
    status: Optional[str] = None,
    brand: Optional[str] = None,
    jatuh_tempo_start: Optional[str] = None,
    jatuh_tempo_end: Optional[str] = None,
    format: str = Query("csv", description="Export format: csv atau excel"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengekspor semua data langganan ke dalam file dengan format yang dipilih (CSV/Excel)."""
    # Validate format
    if format.lower() not in ["csv", "excel", "xlsx"]:
        raise HTTPException(status_code=400, detail="Format tidak valid. Pilih 'csv' atau 'excel'.")

    query = (
        select(LanggananModel)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
        .join(LanggananModel.pelanggan)
    )

    if search:
        query = query.where(PelangganModel.nama.ilike(f"%{search}%"))
    if alamat:
        query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))
    if paket_layanan_name:
        query = query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)
    if status:
        query = query.where(LanggananModel.status == status)


    # Filter berdasarkan brand (JAKINET, JELANTIK, JELANTIK Nagrak, dll)
    if brand:
        query = query.where(PelangganModel.id_brand == brand)

    # Filter berdasarkan tanggal jatuh tempo untuk export
    if jatuh_tempo_start:
        try:
            start_date = datetime.strptime(jatuh_tempo_start, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo >= start_date)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    if jatuh_tempo_end:
        try:
            end_date = datetime.strptime(jatuh_tempo_end, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo <= end_date)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    query = query.order_by(LanggananModel.id.desc())

    result = await db.execute(query)
    langganan_list = result.scalars().unique().all()

    if not langganan_list:
        raise HTTPException(status_code=404, detail="Tidak ada data langganan untuk diekspor dengan filter yang diberikan.")

    # Prepare data untuk export dengan format yang sesuai
    export_data = []
    for langganan in langganan_list:
        export_data.append({
            "id": langganan.id,
            "pelanggan_nama": (langganan.pelanggan.nama if langganan.pelanggan else "N/A"),
            "pelanggan_email": (langganan.pelanggan.email if langganan.pelanggan else "N/A"),
            "pelanggan_no_telp": (format_phone_number(langganan.pelanggan.no_telp) if langganan.pelanggan and langganan.pelanggan.no_telp else "N/A"),
            "pelanggan_alamat": (langganan.pelanggan.alamat if langganan.pelanggan else "N/A"),
            "paket_nama": (langganan.paket_layanan.nama_paket if langganan.paket_layanan else "N/A"),
            "paket_harga": (langganan.paket_layanan.harga if langganan.paket_layanan else 0),
            "status_langganan": langganan.status,
            "tanggal_aktif": langganan.tgl_mulai_langganan,
            "tanggal_jatuh_tempo": langganan.tgl_jatuh_tempo,
            "brand": (langganan.pelanggan.harga_layanan.brand if langganan.pelanggan and langganan.pelanggan.harga_layanan else "N/A"),
        })

    # Gunakan export utility yang sudah dioptimasi
    return create_langganan_export_response(export_data, format.lower())


# GET /langganan/{langganan_id} - Ambil detail langganan
# Buat ambil data detail satu langganan berdasarkan ID
# Path parameters:
# - langganan_id: ID langganan yang mau diambil
# Response: data langganan lengkap dengan relasi pelanggan dan paket layanan
# Error handling: 404 kalau langganan nggak ketemu
# Performance: eager loading biar nggak N+1 query
@router.get("/{langganan_id}", response_model=LanggananSchema)
async def get_langganan_by_id(
    langganan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil detail langganan berdasarkan ID."""
    query = (
        select(LanggananModel)
        .where(LanggananModel.id == langganan_id)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    langganan = result.scalar_one_or_none()

    if not langganan:
        raise HTTPException(status_code=404, detail="Langganan tidak ditemukan")

    # Apply diskon secara dynamic ke harga
    harga_with_diskon = await apply_diskon_to_langganan_price(langganan, db)

    # Create response dict dan override harga_awal
    langganan_dict = LanggananSchema.model_validate(langganan).model_dump(mode='python')
    langganan_dict['harga_awal'] = harga_with_diskon

    return LanggananSchema(**langganan_dict)


# PATCH /langganan/{langganan_id} - Update data langganan
# Buat update data langganan yang udah ada
# Path parameters:
# - langganan_id: ID langganan yang mau diupdate
# Request body: field yang mau diupdate (cuma field yang diisi yang bakal keupdate)
# Response: data langganan setelah diupdate dengan relasi lengkap
# Validation: cek ID langganan harus ada
# Error handling: 404 kalau langganan nggak ketemu
@router.patch("/{langganan_id}", response_model=LanggananSchema)
async def update_langganan(
    langganan_id: int,
    langganan_update: LanggananUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Memperbarui data langganan berdasarkan ID."""
    db_langganan = await db.get(LanggananModel, langganan_id)
    if not db_langganan:
        raise HTTPException(status_code=404, detail="Langganan tidak ditemukan")

    update_data = langganan_update.model_dump(exclude_unset=True)

    # Jika status diubah menjadi "Berhenti", isi tgl_berhenti secara otomatis dan simpan riwayat
    if "status" in update_data and update_data["status"] == "Berhenti":
        hari_ini = date.today()
        update_data["tgl_berhenti"] = hari_ini

        # Simpan riwayat tanggal berhenti
        riwayat_list = []
        if db_langganan.riwayat_tgl_berhenti:
            try:
                riwayat_list = json.loads(db_langganan.riwayat_tgl_berhenti)
            except (json.JSONDecodeError, TypeError):
                riwayat_list = []

        # Menambahkan tanggal berhenti baru ke riwayat
        riwayat_list.append({
            "tanggal": hari_ini.isoformat(),
            "alasan": update_data.get("alasan_berhenti", ""),
            "timestamp": datetime.now().isoformat()
        })

        # Simpan sebagai JSON string
        update_data["riwayat_tgl_berhenti"] = json.dumps(riwayat_list)

        logger.info(f"Langganan ID {langganan_id} status diubah menjadi Berhenti, tgl_berhenti diset ke {hari_ini}, riwayat ditambahkan")

    # Jika status diubah dari "Berhenti" ke status lain, kosongkan tgl_berhenti tapi RIWAYAT TETAP DISIMPAN
    elif "status" in update_data and update_data["status"] != "Berhenti" and db_langganan.status == "Berhenti":
        update_data["tgl_berhenti"] = None
        # RIWAYAT TIDAK DIHAPUS, tetap disimpan untuk histori
        logger.info(f"Langganan ID {langganan_id} status diubah dari Berhenti, tgl_berhenti dikosongkan, riwayat tetap dipertahankan")

    for key, value in update_data.items():
        setattr(db_langganan, key, value)

    db.add(db_langganan)
    await db.commit()

    query = (
        select(LanggananModel)
        .where(LanggananModel.id == db_langganan.id)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    updated_langganan = result.scalar_one()

    return updated_langganan


# DELETE /langganan/{langganan_id} - Hapus langganan
# Buat hapus data langganan dari sistem
# Path parameters:
# - langganan_id: ID langganan yang mau dihapus
# Response: 204 No Content (sukses tapi nggak ada response body)
# Warning: HATI-HATI! Ini akan hapus langganan permanen
# Error handling: 404 kalau langganan nggak ketemu
# Note: Invoice yang berelasi mungkin masih ada (cek constraint di database)
@router.delete("/{langganan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_langganan(
    langganan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Menghapus langganan berdasarkan ID."""
    db_langganan = await db.get(LanggananModel, langganan_id)
    if not db_langganan:
        raise HTTPException(status_code=404, detail="Langganan tidak ditemukan")

    await db.delete(db_langganan)
    await db.commit()
    return None


# --- Endpoint Kalkulasi Prorate ---


class LanggananCalculateRequest(BaseModel):
    paket_layanan_id: int
    metode_pembayaran: str
    pelanggan_id: int
    tgl_mulai: date = Field(default_factory=date.today)


class LanggananCalculateResponse(BaseModel):
    harga_awal: float
    tgl_jatuh_tempo: date


# POST /langganan/calculate-price - Kalkulasi harga langganan
# Buat hitung harga awal dan tanggal jatuh tempo sebelum buat langganan
# Request body: pelanggan_id, paket_layanan_id, metode_pembayaran, tgl_mulai
# Response: harga_awal (sudah include pajak) dan tgl_jatuh_tempo
# Fitur:
# - Otomatis: harga penuh + jatuh tempo tanggal 1 bulan depan
# - Prorate: harga proporsional sisa bulan ini + jatuh tempo akhir bulan
# - Include pajak dari brand pelanggan
# Use case: buat preview harga di frontend sebelum submit
@router.post("/calculate-price", response_model=LanggananCalculateResponse)
async def calculate_langganan_price(
    request_data: LanggananCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Menghitung harga awal dan tanggal jatuh tempo untuk frontend."""
    pelanggan = await db.get(
        PelangganModel,
        request_data.pelanggan_id,
        options=[joinedload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(status_code=404, detail="Data Brand pelanggan tidak ditemukan.")

    paket = await db.get(PaketLayananModel, request_data.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan.")

    start_date = request_data.tgl_mulai

    harga_paket = float(paket.harga)
    pajak_persen = float(pelanggan.harga_layanan.pajak)
    harga_awal_final = 0.0
    tgl_jatuh_tempo_final = None

    if request_data.metode_pembayaran == "Otomatis":
        harga_awal_final = harga_paket * (1 + (pajak_persen / 100))
        tgl_jatuh_tempo_final = (start_date + relativedelta(months=1)).replace(day=1)

    elif request_data.metode_pembayaran == "Prorate":
        _, last_day_of_month = monthrange(start_date.year, start_date.month)
        remaining_days = last_day_of_month - start_date.day + 1

        if remaining_days < 0:
            remaining_days = 0

        harga_per_hari = harga_paket / last_day_of_month
        prorated_price_before_tax = harga_per_hari * remaining_days
        harga_awal_final = prorated_price_before_tax * (1 + (pajak_persen / 100))
        tgl_jatuh_tempo_final = date(start_date.year, start_date.month, last_day_of_month)

    return LanggananCalculateResponse(
        harga_awal=round(harga_awal_final, 0), tgl_jatuh_tempo=tgl_jatuh_tempo_final  # type: ignore
    )


# --- Endpoint untuk Import, Export, dan Template CSV ---


# GET /langganan/template/csv - Download template CSV untuk import langganan
# Buat download file template CSV yang bisa dipakai buat import data langganan
# Response: file CSV dengan header dan contoh data
# Format file: CSV dengan BOM (biar compatibility dengan Excel)
# Header: email_pelanggan, id_brand, nama_paket_layanan, status, metode_pembayaran, tgl_jatuh_tempo
# Contoh data: include sample data biar gampang ngikutin format
@router.get("/template/csv", response_class=StreamingResponse)
async def download_csv_template_langganan():
    """Men-download template CSV untuk import langganan."""
    output = io.StringIO()
    output.write("\ufeff")
    headers = [
        "email_pelanggan",
        "id_brand",
        "nama_paket_layanan",
        "status",
        "metode_pembayaran",
        "tgl_jatuh_tempo",
    ]
    sample_data = [
        {
            "email_pelanggan": "budi.s@example.com",
            "id_brand": "ajn-01",
            "nama_paket_layanan": "Internet 50 Mbps",
            "status": "Aktif",
            "metode_pembayaran": "Otomatis",
            "tgl_jatuh_tempo": "2025-08-01",
        }
    ]

    writer = csv.DictWriter(output, fieldnames=headers, delimiter=";")
    writer.writeheader()
    writer.writerows(sample_data)
    output.seek(0)

    response_headers = {"Content-Disposition": 'attachment; filename="template_import_langganan.csv"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# GET /langganan/export/csv - Export data langganan ke CSV
# Buat export data langganan ke file CSV dengan filter yang sama seperti list
# Query parameters:
# - search: filter pencarian (sama seperti di list)
# - alamat: filter berdasarkan alamat
# - paket_layanan_name: filter berdasarkan nama paket
# - status: filter berdasarkan status
# - brand: filter berdasarkan brand (JAKINET, JELANTIK, JELANTIK Nagrak, dll)
# - jatuh_tempo_start: filter tanggal jatuh tempo mulai
# - jatuh_tempo_end: filter tanggal jatuh tempo akhir
# Response: file CSV dengan kolom: Nama Pelanggan, Email, Nomor Telepon, Brand, Paket Layanan, Status, Metode Pembayaran, Harga, dll
# Format file: CSV dengan BOM dan timestamp di filename
# Performance: eager loading biar efficient
@router.get("/export", response_class=StreamingResponse)
async def export_langganan(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_name: Optional[str] = None,
    status: Optional[str] = None,
    brand: Optional[str] = None,
    jatuh_tempo_start: Optional[str] = None,
    jatuh_tempo_end: Optional[str] = None,
    format: str = Query("csv", description="Export format: csv atau excel"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengekspor semua data langganan ke dalam file dengan format yang dipilih (CSV/Excel)."""
    # Validate format
    if format.lower() not in ["csv", "excel", "xlsx"]:
        raise HTTPException(status_code=400, detail="Format tidak valid. Pilih 'csv' atau 'excel'.")
    query = (
        select(LanggananModel)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
        .join(LanggananModel.pelanggan)
    )

    if search:
        query = query.where(PelangganModel.nama.ilike(f"%{search}%"))
    if alamat:
        query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))
    if paket_layanan_name:
        query = query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)
    if status:
        query = query.where(LanggananModel.status == status)

    
    # Filter berdasarkan brand (JAKINET, JELANTIK, JELANTIK Nagrak, dll)
    if brand:
        query = query.where(PelangganModel.id_brand == brand)

    # Filter berdasarkan tanggal jatuh tempo untuk export
    if jatuh_tempo_start:
        try:
            start_date = datetime.strptime(jatuh_tempo_start, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo >= start_date)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    if jatuh_tempo_end:
        try:
            end_date = datetime.strptime(jatuh_tempo_end, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo <= end_date)
        except ValueError:
            # Skip filter jika format tanggal tidak valid
            pass

    query = query.order_by(LanggananModel.id.desc())

    result = await db.execute(query)
    langganan_list = result.scalars().unique().all()

    if not langganan_list:
        raise HTTPException(status_code=404, detail="Tidak ada data langganan untuk diekspor dengan filter yang diberikan.")

    # Prepare data untuk export dengan format yang sesuai
    export_data = []
    for langganan in langganan_list:
        export_data.append({
            "id": langganan.id,
            "pelanggan_nama": (langganan.pelanggan.nama if langganan.pelanggan else "N/A"),
            "pelanggan_email": (langganan.pelanggan.email if langganan.pelanggan else "N/A"),
            "pelanggan_no_telp": (format_phone_number(langganan.pelanggan.no_telp) if langganan.pelanggan and langganan.pelanggan.no_telp else "N/A"),
            "pelanggan_alamat": (langganan.pelanggan.alamat if langganan.pelanggan else "N/A"),
            "paket_nama": (langganan.paket_layanan.nama_paket if langganan.paket_layanan else "N/A"),
            "paket_harga": (langganan.paket_layanan.harga if langganan.paket_layanan else 0),
            "status_langganan": langganan.status,
            "tanggal_aktif": langganan.tgl_mulai_langganan,
            "tanggal_jatuh_tempo": langganan.tgl_jatuh_tempo,
            "brand": (langganan.pelanggan.harga_layanan.brand if langganan.pelanggan and langganan.pelanggan.harga_layanan else "N/A"),
        })

    # Gunakan export utility yang sudah dioptimasi
    return create_langganan_export_response(export_data, format.lower())


# GET /langganan/export/excel/multi-sheet - Export data langganan dengan multi-sheet Excel
# Buat export data langganan lengkap dengan history pembayaran dan invoice dalam multiple sheets
# Query parameters:
# - search: filter pencarian (sama seperti di list)
# - alamat: filter berdasarkan alamat
# - paket_layanan_name: filter berdasarkan nama paket
# - status: filter berdasarkan status
# - brand: filter berdasarkan brand (JAKINET, JELANTIK, dll)
# - jatuh_tempo_start: filter tanggal jatuh tempo mulai
# - jatuh_tempo_end: filter tanggal jatuh tempo akhir
# - limit: batas maksimal data (default: 5000, max: 10000)
# Response: file Excel dengan 3 sheets:
#   - Sheet 1: Data Langganan (pelanggan + paket + status)
#   - Sheet 2: History Pembayaran per Pelanggan
#   - Sheet 3: History Invoice per Pelanggan
# Performance: batch queries untuk avoid N+1 problem, limit max 10000 records
@router.get("/export/excel/multi-sheet", response_class=StreamingResponse)
async def export_langganan_multi_sheet(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_name: Optional[str] = None,
    status: Optional[str] = None,
    brand: Optional[str] = None,
    jatuh_tempo_start: Optional[str] = None,
    jatuh_tempo_end: Optional[str] = None,
    limit: int = Query(default=5000, le=10000, description="Maximum records to export (max: 10000)"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mengekspor data langganan lengkap dengan history pembayaran dan invoice
    dalam format Excel multi-sheet.

    Sheets:
    - Data Langganan: Informasi langganan dan pelanggan
    - History Pembayaran: Riwayat pembayaran yang sudah lunas
    - History Invoice: Semua riwayat invoice (lunas/belum/expire)

    Performance note: Export dibatasi maksimal 10,000 records.
    """
    # Validate limit
    if limit > 10000:
        raise HTTPException(status_code=400, detail="Maximum 10,000 records allowed per export")

    # Build base query (reuse existing logic)
    query = (
        select(LanggananModel)
        .options(
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
            joinedload(LanggananModel.paket_layanan),
        )
        .join(LanggananModel.pelanggan)
    )

    # Apply filters
    if search:
        query = query.where(PelangganModel.nama.ilike(f"%{search}%"))
    if alamat:
        query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))
    if paket_layanan_name:
        query = query.join(PaketLayananModel).where(PaketLayananModel.nama_paket == paket_layanan_name)
    if status:
        query = query.where(LanggananModel.status == status)
    if brand:
        query = query.where(PelangganModel.id_brand == brand)

    # Filter berdasarkan tanggal jatuh tempo
    if jatuh_tempo_start:
        try:
            start_date = datetime.strptime(jatuh_tempo_start, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo >= start_date)
        except ValueError:
            pass

    if jatuh_tempo_end:
        try:
            end_date = datetime.strptime(jatuh_tempo_end, "%Y-%m-%d").date()
            query = query.where(LanggananModel.tgl_jatuh_tempo <= end_date)
        except ValueError:
            pass

    # Apply ordering and limit
    query = query.order_by(LanggananModel.id.desc()).limit(limit)

    # Execute query
    result = await db.execute(query)
    langganan_list = result.scalars().unique().all()

    if not langganan_list:
        raise HTTPException(status_code=404, detail="Tidak ada data langganan untuk diekspor dengan filter yang diberikan.")

    # Collect pelanggan_ids untuk batch query invoices
    pelanggan_ids = [l.pelanggan_id for l in langganan_list if l.pelanggan_id]

    # Batch query untuk semua invoice (avoid N+1 problem)
    invoices_query = (
        select(InvoiceModel)
        .options(joinedload(InvoiceModel.pelanggan))
        .where(InvoiceModel.pelanggan_id.in_(pelanggan_ids))
        .order_by(InvoiceModel.pelanggan_id, InvoiceModel.tgl_invoice.desc())
    )
    invoices_result = await db.execute(invoices_query)
    invoices = invoices_result.scalars().unique().all()

    # Prepare data untuk Sheet 1: Data Langganan
    sheet1_data = []
    for langganan in langganan_list:
        sheet1_data.append({
            "ID Langganan": str(langganan.id) if langganan.id else "",
            "Nama Pelanggan": langganan.pelanggan.nama if langganan.pelanggan else "N/A",
            "Email": langganan.pelanggan.email if langganan.pelanggan else "N/A",
            "No Telepon": format_phone_number(langganan.pelanggan.no_telp) if langganan.pelanggan and langganan.pelanggan.no_telp else "N/A",
            "Alamat": langganan.pelanggan.alamat if langganan.pelanggan else "N/A",
            "Paket": langganan.paket_layanan.nama_paket if langganan.paket_layanan else "N/A",
            "Harga Paket": float(langganan.paket_layanan.harga) if langganan.paket_layanan else 0,
            "Status Langganan": langganan.status,
            "Tanggal Aktif": langganan.tgl_mulai_langganan,
            "Jatuh Tempo": langganan.tgl_jatuh_tempo,
            "Brand": langganan.pelanggan.harga_layanan.brand if langganan.pelanggan and langganan.pelanggan.harga_layanan else "N/A",
            "Metode Pembayaran": langganan.metode_pembayaran,
        })

    # Prepare data untuk Sheet 2: History Pembayaran (hanya yang lunas)
    sheet2_data = []
    for invoice in invoices:
        if invoice.paid_at:  # Hanya invoice yang sudah dibayar
            # Get metode pembayaran dengan beberapa fallback options
            metode_pembayaran = invoice.metode_pembayaran
            if not metode_pembayaran or metode_pembayaran.strip() == "":
                # Fallback 1: Gunakan xendit_status sebagai indikator
                if invoice.xendit_status and invoice.xendit_status != "pending":
                    metode_pembayaran = f"Xendit ({invoice.xendit_status})"
                # Fallback 2: Gunakan invoice_type
                elif invoice.invoice_type:
                    metode_pembayaran = f"Transfer ({invoice.invoice_type.capitalize()})"
                # Fallback 3: Default
                else:
                    metode_pembayaran = "Xendit Payment Gateway"

            sheet2_data.append({
                "Nama Pelanggan": invoice.pelanggan.nama if invoice.pelanggan else "N/A",
                "Email": invoice.email or (invoice.pelanggan.email if invoice.pelanggan else "N/A"),
                "No Invoice": invoice.invoice_number,
                "Tanggal Bayar": invoice.paid_at,
                "Jumlah Dibayar": float(invoice.paid_amount) if invoice.paid_amount else float(invoice.total_harga),
                "Metode Pembayaran": metode_pembayaran,
                "Status Pembayaran": "Lunas",
            })

    # Prepare data untuk Sheet 3: History Invoice (semua invoice)
    sheet3_data = []
    for invoice in invoices:
        sheet3_data.append({
            "Nama Pelanggan": invoice.pelanggan.nama if invoice.pelanggan else "N/A",
            "Email": invoice.email or (invoice.pelanggan.email if invoice.pelanggan else "N/A"),
            "No Invoice": invoice.invoice_number,
            "Tanggal Invoice": invoice.tgl_invoice,
            "Jatuh Tempo": invoice.tgl_jatuh_tempo,
            "Total Harga": float(invoice.total_harga),
            "Status Invoice": invoice.status_invoice,
            "Tipe Invoice": invoice.invoice_type,
        })

    # Prepare data untuk Sheet 4: Summary Statistics
    # Hitung agregasi data untuk pivot table-like summary
    total_invoices = len(invoices)
    total_langganan = len(langganan_list)

    # Hitung total nilai semua invoice
    total_nilai_semua = sum(float(inv.total_harga or 0) for inv in invoices)

    # Hitung per status invoice
    invoice_lunas = [inv for inv in invoices if inv.status_invoice == "Lunas"]
    invoice_belum_bayar = [inv for inv in invoices if inv.status_invoice == "Belum Dibayar"]
    invoice_expired = [inv for inv in invoices if inv.status_invoice == "Expired"]
    invoice_batal = [inv for inv in invoices if inv.status_invoice == "Batal"]

    # Hitung total nilai per status
    total_nilai_lunas = sum(float(inv.total_harga or 0) for inv in invoice_lunas)
    total_nilai_belum_bayar = sum(float(inv.total_harga or 0) for inv in invoice_belum_bayar)
    total_nilai_expired = sum(float(inv.total_harga or 0) for inv in invoice_expired)
    total_nilai_batal = sum(float(inv.total_harga or 0) for inv in invoice_batal)

    # Hitung persentase
    def calc_persentase(jumlah: int, total: int) -> float:
        return (jumlah / total * 100) if total > 0 else 0.0

    sheet4_data = [
        # Summary User/Langganan
        {
            "Kategori": "Total User/Pelanggan",
            "Jumlah": total_langganan,
            "Persentase": 100.0,
            "Total Nilai": 0,
        },
        {
            "Kategori": "Langganan Aktif",
            "Jumlah": len([l for l in langganan_list if l.status == "Aktif"]),
            "Persentase": calc_persentase(len([l for l in langganan_list if l.status == "Aktif"]), total_langganan),
            "Total Nilai": 0,
        },
        {
            "Kategori": "Langganan Suspended",
            "Jumlah": len([l for l in langganan_list if l.status == "Suspended"]),
            "Persentase": calc_persentase(len([l for l in langganan_list if l.status == "Suspended"]), total_langganan),
            "Total Nilai": 0,
        },
        {
            "Kategori": "Langganan Berhenti",
            "Jumlah": len([l for l in langganan_list if l.status == "Berhenti"]),
            "Persentase": calc_persentase(len([l for l in langganan_list if l.status == "Berhenti"]), total_langganan),
            "Total Nilai": 0,
        },
        {},  # Empty row separator
        # Summary Invoice
        {
            "Kategori": "Total Invoice Terbit",
            "Jumlah": total_invoices,
            "Persentase": 100.0,
            "Total Nilai": total_nilai_semua,
        },
        {
            "Kategori": "Invoice Lunas",
            "Jumlah": len(invoice_lunas),
            "Persentase": calc_persentase(len(invoice_lunas), total_invoices),
            "Total Nilai": total_nilai_lunas,
        },
        {
            "Kategori": "Invoice Belum Dibayar",
            "Jumlah": len(invoice_belum_bayar),
            "Persentase": calc_persentase(len(invoice_belum_bayar), total_invoices),
            "Total Nilai": total_nilai_belum_bayar,
        },
        {
            "Kategori": "Invoice Expired",
            "Jumlah": len(invoice_expired),
            "Persentase": calc_persentase(len(invoice_expired), total_invoices),
            "Total Nilai": total_nilai_expired,
        },
        {
            "Kategori": "Invoice Batal",
            "Jumlah": len(invoice_batal),
            "Persentase": calc_persentase(len(invoice_batal), total_invoices),
            "Total Nilai": total_nilai_batal,
        },
        {},  # Empty row separator
        # Summary Pembayaran
        {
            "Kategori": "Total Pembayaran Masuk",
            "Jumlah": len(invoice_lunas),
            "Persentase": calc_persentase(len(invoice_lunas), total_invoices) if total_invoices > 0 else 0,
            "Total Nilai": total_nilai_lunas,
        },
        {
            "Kategori": "Outstanding (Belum Dibayar)",
            "Jumlah": len(invoice_belum_bayar),
            "Persentase": calc_persentase(len(invoice_belum_bayar), total_invoices) if total_invoices > 0 else 0,
            "Total Nilai": total_nilai_belum_bayar,
        },
    ]

    # Combine semua sheets
    sheets_data = {
        "Data Langganan": sheet1_data,
        "History Pembayaran": sheet2_data,
        "History Invoice": sheet3_data,
        "Summary Statistics": sheet4_data,
    }

    # Gunakan multi-sheet export utility
    return create_langganan_multi_sheet_export_response(sheets_data)


# POST /langganan/import/csv - Import data langganan dari CSV
# Buat import data langganan dari file CSV
# Request body: file CSV dengan format yang sesuai template
# Response: jumlah langganan yang berhasil diimport + error message kalau ada
# Validation:
# - cek format file (.csv)
# - cek email pelanggan harus ada di database
# - cek paket layanan dan brand harus ada
# - cek duplikasi email (dalam file dan database)
# - cek pelanggan belum punya langganan
# - cek format tanggal (YYYY-MM-DD)
# Error handling: rollback semua data kalau ada error, return detail error per baris
# Performance: batch insert biar lebih cepat, eager loading buat validation
@router.post("/import/csv")
async def import_from_csv_langganan(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengimpor data langganan dari file CSV."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    contents = await file.read()
    try:
        content_str = contents.decode(chardet.detect(contents)["encoding"] or "utf-8")
        
        # Hapus BOM jika ada
        if content_str.startswith("\ufeff"):
            content_str = content_str.lstrip("\ufeff")

        # --- DETEKSI DELIMITER ---
        first_line = content_str.split('\n')[0]
        dialect_delimiter = ","
        if ";" in first_line and first_line.count(";") > first_line.count(","):
            dialect_delimiter = ";"

        reader_object = csv.DictReader(io.StringIO(content_str), delimiter=dialect_delimiter)
        reader = list(reader_object)
    except Exception:
        raise HTTPException(status_code=400, detail="Encoding file tidak dapat dibaca atau format CSV tidak valid.")
    errors = []
    langganan_to_create = []
    processed_emails_in_file = set()
    skipped_rows = 0

    emails_to_find = {row.get("email_pelanggan", "").lower().strip() for row in reader if row.get("email_pelanggan")}
    paket_names_to_find = {
        row.get("nama_paket_layanan", "").lower().strip() for row in reader if row.get("nama_paket_layanan")
    }
    brand_ids_to_find = {row.get("id_brand", "").strip() for row in reader if row.get("id_brand")}

    pelanggan_q = await db.execute(
        select(PelangganModel)
        .options(joinedload(PelangganModel.harga_layanan))
        .where(func.lower(PelangganModel.email).in_(emails_to_find))
    )
    pelanggan_map = {p.email.lower(): p for p in pelanggan_q.scalars().unique().all()}

    paket_q = await db.execute(
        select(PaketLayananModel).where(
            func.lower(PaketLayananModel.nama_paket).in_(paket_names_to_find),
            PaketLayananModel.id_brand.in_(brand_ids_to_find),
        )
    )
    paket_map = {(p.nama_paket.lower(), p.id_brand): p for p in paket_q.scalars().all()}

    pelanggan_ids_found = [p.id for p in pelanggan_map.values()]
    existing_langganan_q = await db.execute(
        select(LanggananModel.pelanggan_id).where(LanggananModel.pelanggan_id.in_(pelanggan_ids_found))
    )
    subscribed_pelanggan_ids = set(existing_langganan_q.scalars().all())

    # OPTIMIZATION: Batch query untuk DataTeknis agar tidak N+1
    data_teknis_q = await db.execute(
        select(DataTeknisModel).where(DataTeknisModel.pelanggan_id.in_(pelanggan_ids_found))
    )
    data_teknis_map = {dt.pelanggan_id: dt for dt in data_teknis_q.scalars().all()}

    for row_num, row in enumerate(reader, start=2):
        # Skip baris jika benar-benar kosong (tidak ada data sama sekali)
        if not any(row.values()):
            skipped_rows += 1
            continue

        try:
            data_import = LanggananImport(**row)  # type: ignore

            # Validasi duplikat email dalam file CSV yang sama
            email_lower = data_import.email_pelanggan.lower()
            if email_lower in processed_emails_in_file:
                errors.append(f"Baris {row_num}: Email '{data_import.email_pelanggan}' duplikat di dalam file CSV.")
                continue
            processed_emails_in_file.add(email_lower)

            pelanggan = pelanggan_map.get(data_import.email_pelanggan.lower())
            if not pelanggan:
                errors.append(f"Baris {row_num}: Pelanggan dengan email '{data_import.email_pelanggan}' tidak ditemukan.")
                continue

            paket_key = (data_import.nama_paket_layanan.lower(), data_import.id_brand)
            paket = paket_map.get(paket_key)
            if not paket:
                errors.append(
                    f"Baris {row_num}: Paket Layanan '{data_import.nama_paket_layanan}' untuk brand '{data_import.id_brand}' tidak ditemukan."
                )
                continue

            if pelanggan.id in subscribed_pelanggan_ids:
                errors.append(f"Baris {row_num}: Pelanggan '{pelanggan.nama}' sudah memiliki langganan.")
                continue

            # OPTIMIZED: Cek data teknis dari batch query (tidak N+1 lagi)
            data_teknis = data_teknis_map.get(pelanggan.id)

            if not data_teknis:
                errors.append(f"Baris {row_num}: Pelanggan '{pelanggan.nama}' belum memiliki data teknis. Tim NOC harus menambahkan data teknis terlebih dahulu sebelum langganan dapat dibuat.")
                continue

            # Konversi string tanggal ke objek date jika tidak None
            tgl_jatuh_tempo_value = None
            if data_import.tgl_jatuh_tempo:
                if isinstance(data_import.tgl_jatuh_tempo, str):
                    try:
                        tgl_jatuh_tempo_value = datetime.strptime(data_import.tgl_jatuh_tempo, "%Y-%m-%d").date()
                    except ValueError:
                        # Jika format tanggal tidak valid, lewati baris ini
                        errors.append(
                            f"Baris {row_num}: Format tanggal tidak valid untuk tgl_jatuh_tempo: '{data_import.tgl_jatuh_tempo}'"
                        )
                        continue
                else:
                    tgl_jatuh_tempo_value = data_import.tgl_jatuh_tempo

            # Hitung harga include PPN (sama seperti create langganan manual)
            harga_paket = float(paket.harga)
            pajak_persen = float(pelanggan.harga_layanan.pajak) if pelanggan.harga_layanan else 0.0
            harga_dengan_ppn = harga_paket * (1 + (pajak_persen / 100))

            new_langganan_data = {
                "pelanggan_id": pelanggan.id,
                "paket_layanan_id": paket.id,
                "status": data_import.status,
                "metode_pembayaran": data_import.metode_pembayaran,
                "harga_awal": round(harga_dengan_ppn, 0),
                "tgl_jatuh_tempo": tgl_jatuh_tempo_value,
            }
            langganan_to_create.append(LanggananModel(**new_langganan_data))

        except ValidationError as e:
            error_messages = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
            errors.append(f"Baris {row_num}: {error_messages}")
        except Exception as e:
            errors.append(f"Baris {row_num}: Terjadi error - {str(e)}")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Impor gagal, ditemukan error.", "errors": errors},
        )

    if not langganan_to_create:
        raise HTTPException(status_code=400, detail="Tidak ada data valid untuk diimpor.")

    try:
        db.add_all(langganan_to_create)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {e}")

    success_message = f"Berhasil mengimpor {len(langganan_to_create)} langganan baru."
    if skipped_rows > 0:
        success_message += f" {skipped_rows} baris kosong dilewati."

    logger.info(f"Import CSV langganan selesai: {len(langganan_to_create)} berhasil, {len(errors)} error, {skipped_rows} baris kosong dilewati")

    return {"message": success_message}


# --- ONE-TIME FIX: Perbaiki harga langganan yang diimport tanpa PPN ---


@router.post("/fix-imported-prices")
async def fix_imported_langganan_prices(
    dry_run: bool = Query(True, description="True = preview saja, False = benar-benar update"),
    alamat: Optional[str] = Query(None, description="Filter berdasarkan alamat pelanggan (contoh: 'Pulogebang')"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    ONE-TIME FIX: Memperbaiki harga langganan yang diimport tanpa PPN.
    
    Cara kerja:
    - Cari semua langganan dimana harga_awal == harga paket (tanpa PPN)
    - Update harga_awal menjadi harga paket + PPN
    
    Parameter:
    - dry_run=true (default): Preview data yang akan diupdate, TANPA mengubah apapun
    - dry_run=false: Benar-benar update harga ke database
    - alamat: Filter berdasarkan alamat pelanggan (opsional, contoh: 'Pulogebang')
    """
    # Query semua langganan dengan relasi paket dan pelanggan (untuk pajak)
    query = (
        select(LanggananModel)
        .join(LanggananModel.pelanggan)
        .options(
            joinedload(LanggananModel.paket_layanan),
            joinedload(LanggananModel.pelanggan).joinedload(PelangganModel.harga_layanan),
        )
    )

    # Filter berdasarkan alamat jika diberikan
    if alamat:
        query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))

    result = await db.execute(query)
    all_langganan = result.scalars().unique().all()

    affected = []
    for langganan in all_langganan:
        if not langganan.paket_layanan or not langganan.pelanggan or not langganan.pelanggan.harga_layanan:
            continue

        harga_paket = float(langganan.paket_layanan.harga)
        harga_awal = float(langganan.harga_awal) if langganan.harga_awal else 0.0
        pajak_persen = float(langganan.pelanggan.harga_layanan.pajak)

        # Cek apakah harga_awal sama dengan harga paket (tanpa PPN)
        # Toleransi Rp 1 untuk masalah pembulatan
        if pajak_persen > 0 and abs(harga_awal - harga_paket) < 1:
            harga_baru = round(harga_paket * (1 + (pajak_persen / 100)), 0)

            affected.append({
                "langganan_id": langganan.id,
                "pelanggan_nama": langganan.pelanggan.nama if langganan.pelanggan else "N/A",
                "alamat": langganan.pelanggan.alamat if langganan.pelanggan else "N/A",
                "brand": langganan.pelanggan.harga_layanan.brand if langganan.pelanggan.harga_layanan else "N/A",
                "paket": langganan.paket_layanan.nama_paket,
                "harga_paket": harga_paket,
                "pajak_persen": pajak_persen,
                "harga_lama": harga_awal,
                "harga_baru": harga_baru,
                "selisih": harga_baru - harga_awal,
            })

            if not dry_run:
                langganan.harga_awal = harga_baru
                db.add(langganan)

    if not dry_run and affected:
        await db.commit()
        logger.info(f"🔧 FIX IMPORTED PRICES: {len(affected)} langganan berhasil diupdate dengan PPN (filter alamat: {alamat or 'semua'})")

    filter_info = f" (filter: alamat '{alamat}')" if alamat else ""
    return {
        "mode": "PREVIEW (dry_run)" if dry_run else "UPDATED",
        "total_affected": len(affected),
        "filter_alamat": alamat or "Semua",
        "message": f"{'Preview' if dry_run else 'Berhasil update'} {len(affected)} langganan yang harganya belum include PPN{filter_info}.",
        "hint": "Jalankan dengan dry_run=false untuk benar-benar update." if dry_run else "Harga sudah diupdate!",
        "data": affected,
    }


# INVOICE GABUNGAN PRORATE + HARGA PAKET BUAT 2 BULAN


class LanggananCalculateProratePlusFullResponse(BaseModel):
    harga_prorate: float
    harga_normal: float
    harga_total_awal: float
    tgl_jatuh_tempo: date


# POST /langganan/calculate-prorate-plus-full - Kalkulasi harga gabungan (prorate + bulan depan)
# Buat hitung harga prorate bulan ini + harga penuh bulan depan (buat invoice gabungan)
# Request body: pelanggan_id, paket_layanan_id, metode_pembayaran, tgl_mulai
# Response: harga_prorate, harga_normal, harga_total_awal, tgl_jatuh_tempo
# Fitur:
# - harga_prorate: harga proporsional sisa bulan ini (include pajak)
# - harga_normal: harga penuh bulan depan (include pajak)
# - harga_total_awal: total harga gabungan
# - tgl_jatuh_tempo: akhir bulan ini
# Use case: buat preview harga invoice gabungan di frontend
@router.post(
    "/calculate-prorate-plus-full",
    response_model=LanggananCalculateProratePlusFullResponse,
)
async def calculate_langganan_price_plus_full(
    request_data: LanggananCalculateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menghitung harga gabungan: prorate bulan ini + harga penuh bulan depan.
    """
    pelanggan = await db.get(
        PelangganModel,
        request_data.pelanggan_id,
        options=[joinedload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(status_code=404, detail="Data Brand pelanggan tidak ditemukan.")

    paket = await db.get(PaketLayananModel, request_data.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan.")

    start_date = request_data.tgl_mulai
    harga_paket = float(paket.harga)
    pajak_persen = float(pelanggan.harga_layanan.pajak)

    harga_normal_full = harga_paket * (1 + (pajak_persen / 100))

    _, last_day_of_month = monthrange(start_date.year, start_date.month)
    remaining_days = last_day_of_month - start_date.day + 1
    if remaining_days < 0:
        remaining_days = 0

    harga_per_hari = harga_paket / last_day_of_month
    prorated_price_before_tax = harga_per_hari * remaining_days
    harga_prorate_final = prorated_price_before_tax * (1 + (pajak_persen / 100))

    harga_total_final = harga_prorate_final + harga_normal_full

    tgl_jatuh_tempo_final = date(start_date.year, start_date.month, last_day_of_month)

    return LanggananCalculateProratePlusFullResponse(
        harga_prorate=round(harga_prorate_final, 0),
        harga_normal=round(harga_normal_full, 0),
        harga_total_awal=round(harga_total_final, 0),
        tgl_jatuh_tempo=tgl_jatuh_tempo_final,
    )


# GET /langganan/count - Hitung total jumlah langganan
# Buat ngambil total jumlah langganan di database
# Response: integer (total count)
# Use case: buat dashboard atau statistik
# Performance: simple count query, efficient
@router.get("/count", response_model=int)
async def get_langganan_count(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menghitung total jumlah langganan.
    """
    count_query = select(func.count(LanggananModel.id))
    result = await db.execute(count_query)
    total_count = result.scalar_one()
    return total_count


# GET /langganan/pelanggan/list - Ambil semua pelanggan dengan status langganan
# Buat nampilin list pelanggan plus status langganan mereka (ada/nggak)
# Response: list pelanggan dengan field has_subscription (boolean)
# Use case: buat nampilin pelanggan di dropdown atau list dengan indikator status langganan
# Performance: eager loading langganan relasi biar efficient
@router.get("/pelanggan/list", response_model=List[PelangganSchema])
async def get_all_pelanggan_with_status(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mengambil daftar semua pelanggan, dengan status langganan dan data teknis mereka.
    Info penting untuk Finance: hanya pelanggan dengan data teknis yang bisa dibuatkan langganan.
    """
    result = await db.execute(
        select(PelangganModel)
        .options(
            joinedload(PelangganModel.langganan),
            joinedload(PelangganModel.data_teknis)
        )
        .order_by(PelangganModel.nama)
    )
    pelanggan = result.scalars().unique().all()

    for p in pelanggan:
        p.has_subscription = len(p.langganan) > 0
        # Menambahkan informasi apakah pelanggan sudah punya data teknis
        p.has_data_teknis = len(p.data_teknis) > 0 if hasattr(p, 'data_teknis') and p.data_teknis else False

    return pelanggan


# POST /langganan/sync-suspended - Sync semua suspended langganan ke Mikrotik
# Endpoint buat sinkronisasi manual semua langganan yang statusnya Suspended
# Response: summary hasil sinkronisasi
# Fitur:
# - Cari semua langganan dengan status "Suspended"
# - Update status Mikrotik (disable PPPoE secret, set profile SUSPENDED)
# - Hapus koneksi aktif dari Mikrotik
# - Report jumlah success dan failed
# Use case: Fix masalah user yang statusnya Suspended di DB tapi masih aktif di Mikrotik
@router.post("/sync-suspended", status_code=status.HTTP_200_OK)
async def sync_suspended_to_mikrotik(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Sinkronisasi manual semua langganan yang statusnya Suspended ke Mikrotik.
    Endpoint ini digunakan untuk memastikan semua user yang sudah Suspended
    di database juga diblokir di Mikrotik.

    Use case: User sudah jatuh tempo dan statusnya Suspended di database,
    tapi akses internetnya masih aktif karena belum di-sync ke Mikrotik.
    """
    try:
        from ..services import mikrotik_service

        # 1. Cari semua langganan Suspended dengan data teknis
        query = (
            select(LanggananModel)
            .where(LanggananModel.status == "Suspended")
            .options(
                joinedload(LanggananModel.pelanggan).options(
                    joinedload(PelangganModel.data_teknis),
                ),
            )
        )
        result = await db.execute(query)
        suspended_langganans = result.scalars().unique().all()

        if not suspended_langganans:
            return {
                "message": "Tidak ada langganan dengan status Suspended",
                "total_processed": 0,
                "success_count": 0,
                "failed_count": 0
            }

        logger.info(f"🔄 Found {len(suspended_langganans)} suspended langganan to sync with Mikrotik")

        # 2. Proses setiap langganan
        success_count = 0
        failed_count = 0
        failed_details = []

        for langganan in suspended_langganans:
            try:
                data_teknis_list = langganan.pelanggan.data_teknis if hasattr(langganan.pelanggan, 'data_teknis') else []

                if not data_teknis_list:
                    logger.warning(f"⚠️ Langganan ID {langganan.id} ({langganan.pelanggan.nama}) tidak punya data teknis")
                    failed_details.append({
                        "langganan_id": langganan.id,
                        "pelanggan_nama": langganan.pelanggan.nama,
                        "error": "Tidak ada data teknis"
                    })
                    failed_count += 1
                    continue

                data_teknis = data_teknis_list[0]

                if not data_teknis.id_pelanggan:
                    logger.warning(f"⚠️ Langganan ID {langganan.id} ({langganan.pelanggan.nama}) data teknis tidak punya id_pelanggan")
                    failed_details.append({
                        "langganan_id": langganan.id,
                        "pelanggan_nama": langganan.pelanggan.nama,
                        "error": "Data teknis tidak lengkap (id_pelanggan kosong)"
                    })
                    failed_count += 1
                    continue

                # Sync ke Mikrotik dengan status Suspended
                await mikrotik_service.trigger_mikrotik_update(
                    db=db,
                    langganan=langganan,
                    data_teknis=data_teknis,
                    old_id_pelanggan=data_teknis.id_pelanggan
                )

                # Reset flag sync pending jika ada
                if data_teknis.mikrotik_sync_pending:
                    data_teknis.mikrotik_sync_pending = False
                    db.add(data_teknis)

                logger.info(f"✅ Sync SUCCESS: Langganan ID {langganan.id}, Pelanggan: {langganan.pelanggan.nama}, PPPoE: {data_teknis.id_pelanggan}")
                success_count += 1

            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Sync FAILED: Langganan ID {langganan.id}, Pelanggan: {langganan.pelanggan.nama}, Error: {error_msg}")
                failed_details.append({
                    "langganan_id": langganan.id,
                    "pelanggan_nama": langganan.pelanggan.nama,
                    "error": error_msg
                })
                failed_count += 1

        # 3. Commit perubahan
        await db.commit()

        # 4. Return response
        total_processed = len(suspended_langganans)
        response_data = {
            "message": f"Sinkronisasi selesai: {success_count} success, {failed_count} failed dari {total_processed} langganan Suspended",
            "total_processed": total_processed,
            "success_count": success_count,
            "failed_count": failed_count,
            "failed_details": failed_details,
            "logika_bisnis": "User dengan status Suspended akan diblokir akses internetnya melalui Mikrotik (PPPoE secret disabled, profile=SUSPENDED)"
        }

        logger.info(f"🔄 Bulk sync COMPLETED: {success_count}/{total_processed} langganan berhasil di-sync ke Mikrotik")

        return response_data

    except Exception as e:
        await db.rollback()
        logger.error(f"❌ Bulk sync FAILED: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Gagal sinkronisasi langganan Suspended ke Mikrotik: {str(e)}"
        )


