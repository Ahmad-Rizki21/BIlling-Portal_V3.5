import csv
import io
import logging
from calendar import monthrange
from datetime import date, datetime
from typing import List, Optional

import chardet
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError, Field
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
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

router = APIRouter(prefix="/langganan", tags=["Langganan"])

logger = logging.getLogger(__name__)


# --- Helper Functions ---
def format_phone_number(phone_number: str) -> str:
    """
    Format phone number to international format (62 prefix).
    Converts numbers starting with 0 to 62 format.
    """
    if not phone_number or phone_number.strip() == '':
        return phone_number

    phone = phone_number.strip()

    # Remove any non-digit characters first
    phone_digits = ''.join(c for c in phone if c.isdigit())

    # If starts with 0, replace with 62
    if phone_digits.startswith('0'):
        return '62' + phone_digits[1:]

    # If already starts with 62 or doesn't start with 0, return as is
    return phone_digits


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
async def create_langganan(langganan_data: LanggananCreate, db: AsyncSession = Depends(get_db)):
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
):
    """Mengambil semua langganan dengan opsi filter dan paginasi serta total count."""
    base_query = (
        select(LanggananModel)
        .join(LanggananModel.pelanggan)
        .options(
            joinedload(LanggananModel.pelanggan).options(
                joinedload(PelangganModel.langganan),
                joinedload(PelangganModel.harga_layanan),
            ),
            joinedload(LanggananModel.paket_layanan),
        )
    )
    count_query = select(func.count(LanggananModel.id)).join(LanggananModel.pelanggan)

    if for_invoice_selection:
        base_query = base_query.where(LanggananModel.status != "Berhenti")
        count_query = count_query.where(LanggananModel.status != "Berhenti")

    if search:
        filter_condition = PelangganModel.nama.ilike(f"%{search}%")
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

    return LanggananListResponse(data=langganan_list, total_count=total_count)


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

    return langganan


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
):
    """Memperbarui data langganan berdasarkan ID."""
    db_langganan = await db.get(LanggananModel, langganan_id)
    if not db_langganan:
        raise HTTPException(status_code=404, detail="Langganan tidak ditemukan")

    update_data = langganan_update.model_dump(exclude_unset=True)
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
async def delete_langganan(langganan_id: int, db: AsyncSession = Depends(get_db)):
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
async def calculate_langganan_price(request_data: LanggananCalculateRequest, db: AsyncSession = Depends(get_db)):
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

    writer = csv.DictWriter(output, fieldnames=headers)
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
@router.get("/export/csv", response_class=StreamingResponse)
async def export_to_csv_langganan(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_name: Optional[str] = None,
    status: Optional[str] = None,
    brand: Optional[str] = None,
    jatuh_tempo_start: Optional[str] = None,
    jatuh_tempo_end: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Mengekspor semua data langganan ke dalam file CSV dengan filter."""
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

    output = io.StringIO()
    output.write("\ufeff")
    rows_to_write = []
    for langganan in langganan_list:
        rows_to_write.append(
            {
                "Nama Pelanggan": (langganan.pelanggan.nama if langganan.pelanggan else "N/A"),
                "Email Pelanggan": (langganan.pelanggan.email if langganan.pelanggan else "N/A"),
                "Alamat": (langganan.pelanggan.alamat if langganan.pelanggan else "N/A"),
                "Alamat Lengkap": (langganan.pelanggan.alamat_2 if langganan.pelanggan else "N/A"),
                "Nomor Telepon": (format_phone_number(langganan.pelanggan.no_telp) if langganan.pelanggan and langganan.pelanggan.no_telp else "N/A"),
                "Brand": (langganan.pelanggan.harga_layanan.brand if langganan.pelanggan and langganan.pelanggan.harga_layanan else "N/A"),
                "Paket Layanan": (langganan.paket_layanan.nama_paket if langganan.paket_layanan else "N/A"),
                "Status": langganan.status,
                "Metode Pembayaran": langganan.metode_pembayaran,
                "Harga": langganan.harga_awal,
                "Tgl Jatuh Tempo": langganan.tgl_jatuh_tempo,
                "Tgl Invoice Terakhir": langganan.tgl_invoice_terakhir,
            }
        )

    if not rows_to_write:
        raise HTTPException(status_code=404, detail="Tidak ada data valid untuk diekspor.")

    writer = csv.DictWriter(output, fieldnames=rows_to_write[0].keys())
    writer.writeheader()
    writer.writerows(rows_to_write)
    output.seek(0)

    filename = f"export_langganan_{datetime.now().strftime('%Y%m%d')}.csv"
    response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


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
async def import_from_csv_langganan(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Mengimpor data langganan dari file CSV."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    contents = await file.read()
    try:
        content_str = contents.decode(chardet.detect(contents)["encoding"] or "utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="Encoding file tidak dapat dibaca.")

    reader = list(csv.DictReader(io.StringIO(content_str)))
    errors = []
    langganan_to_create = []
    processed_emails_in_file = set()
    skipped_rows = 0

    emails_to_find = {row.get("email_pelanggan", "").lower().strip() for row in reader if row.get("email_pelanggan")}
    paket_names_to_find = {
        row.get("nama_paket_layanan", "").lower().strip() for row in reader if row.get("nama_paket_layanan")
    }
    brand_ids_to_find = {row.get("id_brand", "").strip() for row in reader if row.get("id_brand")}

    pelanggan_q = await db.execute(select(PelangganModel).where(func.lower(PelangganModel.email).in_(emails_to_find)))
    pelanggan_map = {p.email.lower(): p for p in pelanggan_q.scalars().all()}

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

            new_langganan_data = {
                "pelanggan_id": pelanggan.id,
                "paket_layanan_id": paket.id,
                "status": data_import.status,
                "metode_pembayaran": data_import.metode_pembayaran,
                "harga_awal": paket.harga,
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
async def calculate_langganan_price_plus_full(request_data: LanggananCalculateRequest, db: AsyncSession = Depends(get_db)):
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
async def get_langganan_count(db: AsyncSession = Depends(get_db)):
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
async def get_all_pelanggan_with_status(db: AsyncSession = Depends(get_db)):
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
        # Tambahkan informasi apakah pelanggan sudah punya data teknis
        p.has_data_teknis = len(p.data_teknis) > 0 if hasattr(p, 'data_teknis') and p.data_teknis else False

    return pelanggan


