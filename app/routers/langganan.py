import csv
import io
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
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.harga_layanan import HargaLayanan as HargaLayananModel
from ..models.invoice import Invoice as InvoiceModel
from ..models.langganan import Langganan as LanggananModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel
from ..models.pelanggan import Pelanggan as PelangganModel
from ..schemas.langganan import (
    Langganan as LanggananSchema,
    LanggananCreate,
    LanggananImport,
    LanggananUpdate,
)
from ..schemas.pelanggan import Pelanggan as PelangganSchema

router = APIRouter(prefix="/langganan", tags=["Langganan"])


# --- Endpoint Utama untuk Manajemen Langganan ---


@router.post("/", response_model=LanggananSchema, status_code=status.HTTP_201_CREATED)
async def create_langganan(
    langganan_data: LanggananCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat langganan baru dengan perhitungan harga otomatis di backend.
    Mendukung metode pembayaran 'Otomatis' dan 'Prorate' (biasa atau gabungan).
    """
    pelanggan = await db.get(
        PelangganModel,
        langganan_data.pelanggan_id,
        options=[selectinload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(
            status_code=404, detail="Data Brand pelanggan tidak ditemukan."
        )

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

        # ▼▼▼ LOGIKA BARU YANG MEMPERBAIKI MASALAH ANDA ▼▼▼
        if langganan_data.sertakan_bulan_depan:
            # Jika switch aktif, hitung harga gabungan
            harga_normal_full = harga_paket * (1 + (pajak_persen / 100))
            harga_awal_final = harga_prorate_final + harga_normal_full
        else:
            # Jika tidak, gunakan harga prorate saja
            harga_awal_final = harga_prorate_final

        tgl_jatuh_tempo_final = date(
            start_date.year, start_date.month, last_day_of_month
        )

    # Buat objek langganan dengan data yang sudah benar
    db_langganan = LanggananModel(
        pelanggan_id=langganan_data.pelanggan_id,
        paket_layanan_id=langganan_data.paket_layanan_id,
        status=langganan_data.status,
        metode_pembayaran=langganan_data.metode_pembayaran,
        harga_awal=round(harga_awal_final, 0),  # Menyimpan total harga yang benar
        tgl_jatuh_tempo=tgl_jatuh_tempo_final,
        tgl_mulai_langganan=start_date,
    )

    db.add(db_langganan)
    await db.commit()

    # Ambil kembali data yang baru dibuat beserta relasinya untuk memastikan data akurat
    query = (
        select(LanggananModel)
        .where(LanggananModel.id == db_langganan.id)
        .options(
            # Sama seperti di atas, muat relasi secara bersarang
            selectinload(LanggananModel.pelanggan).selectinload(
                PelangganModel.harga_layanan
            ),
            selectinload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    created_langganan = result.scalar_one()

    return created_langganan


@router.get("/", response_model=List[LanggananSchema])
async def get_all_langganan(
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    paket_layanan_id: Optional[int] = None,
    status: Optional[str] = None,
    for_invoice_selection: bool = False,
    skip: int = 0,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Mengambil semua langganan dengan opsi filter dan paginasi."""
    query = (
        select(LanggananModel)
        .join(LanggananModel.pelanggan)
        .options(
            # PERBAIKAN: Muat relasi pelanggan, DAN di dalamnya muat DUA relasi milik pelanggan:
            selectinload(LanggananModel.pelanggan).options(
                selectinload(PelangganModel.langganan),      # <-- Ini untuk logika "NEW USER"
                selectinload(PelangganModel.harga_layanan)   # <-- Mencegah N+1 saat serialisasi
            ),
            # Lanjutkan dengan memuat relasi lainnya di level Langganan
            selectinload(LanggananModel.paket_layanan),
        )
    )

    if for_invoice_selection:
        query = query.where(LanggananModel.status != "Berhenti")

    if search:
        query = query.where(PelangganModel.nama.ilike(f"%{search}%"))
    if alamat: 
        query = query.where(PelangganModel.alamat.ilike(f"%{alamat}%"))
    if paket_layanan_id:
        query = query.where(LanggananModel.paket_layanan_id == paket_layanan_id)
    if status:
        query = query.where(LanggananModel.status == status)

    final_query = query.offset(skip)
    if limit is not None:
        final_query = final_query.limit(limit)

    result = await db.execute(final_query)
    langganan_list = result.scalars().all()
    
    # === OPTIMISASI LOGIKA NEW USER (MENGHINDARI N+1 QUERY) ===
    if for_invoice_selection and langganan_list:
        # 1. Kumpulkan semua ID pelanggan dari hasil query
        pelanggan_ids = {l.pelanggan_id for l in langganan_list}

        # 2. Jalankan SATU query untuk menghitung invoice untuk semua pelanggan tersebut
        invoice_counts_stmt = (
            select(InvoiceModel.pelanggan_id, func.count(InvoiceModel.id).label("count"))
            .where(InvoiceModel.pelanggan_id.in_(pelanggan_ids))
            .group_by(InvoiceModel.pelanggan_id)
        )
        invoice_counts_result = await db.execute(invoice_counts_stmt)
        # Buat map: {pelanggan_id: invoice_count}
        invoice_counts_map = {pid: count for pid, count in invoice_counts_result}

        # 3. Iterasi di Python untuk menetapkan flag (sangat cepat)
        for langganan in langganan_list:
            pelanggan = langganan.pelanggan
            is_new_user = False
            
            if pelanggan and len(pelanggan.langganan) == 1:
                # Ambil hasil dari map, bukan query baru. Default ke 0 jika tidak ada.
                if invoice_counts_map.get(pelanggan.id, 0) == 0:
                    is_new_user = True
            
            # Set flag pada objek langganan
            langganan.is_new_user = is_new_user

    return langganan_list



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

    # Ambil kembali data yang baru dibuat beserta relasinya untuk memastikan data akurat
    query = (
        select(LanggananModel)
        .where(LanggananModel.id == db_langganan.id)
        .options(
            # UBAH BAGIAN INI:
            # Muat relasi pelanggan, DAN di dalamnya muat juga relasi harga_layanan
            selectinload(LanggananModel.pelanggan).selectinload(
                PelangganModel.harga_layanan
            ),
            selectinload(LanggananModel.paket_layanan),
        )
    )
    result = await db.execute(query)
    # Ganti nama variabel agar tidak ambigu
    updated_langganan = result.scalar_one()

    return updated_langganan


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


@router.post("/calculate-price", response_model=LanggananCalculateResponse)
async def calculate_langganan_price(
    request_data: LanggananCalculateRequest, db: AsyncSession = Depends(get_db)
):
    """Menghitung harga awal dan tanggal jatuh tempo untuk frontend."""
    pelanggan = await db.get(
        PelangganModel,
        request_data.pelanggan_id,
        options=[selectinload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(
            status_code=404, detail="Data Brand pelanggan tidak ditemukan."
        )

    paket = await db.get(PaketLayananModel, request_data.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan.")

    # --- PERUBAHAN LOGIKA ---
    # Gunakan tanggal mulai dari request, bukan date.today() secara langsung
    start_date = request_data.tgl_mulai

    harga_paket = float(paket.harga)
    pajak_persen = float(pelanggan.harga_layanan.pajak)
    harga_awal_final = 0.0
    tgl_jatuh_tempo_final = None

    if request_data.metode_pembayaran == "Otomatis":
        harga_awal_final = harga_paket * (1 + (pajak_persen / 100))
        # Jatuh tempo adalah tanggal 1 di bulan berikutnya dari tanggal mulai
        tgl_jatuh_tempo_final = (start_date + relativedelta(months=1)).replace(day=1)

    elif request_data.metode_pembayaran == "Prorate":
        # Perhitungan prorate berdasarkan 'start_date'
        _, last_day_of_month = monthrange(start_date.year, start_date.month)
        # Pastikan kita tidak menghitung hari yang sudah lewat
        remaining_days = last_day_of_month - start_date.day + 1

        # Jika remaining_days negatif (misal, start_date > last_day_of_month), anggap 0
        if remaining_days < 0:
            remaining_days = 0

        harga_per_hari = harga_paket / last_day_of_month
        prorated_price_before_tax = harga_per_hari * remaining_days
        harga_awal_final = prorated_price_before_tax * (1 + (pajak_persen / 100))
        # Jatuh tempo prorate selalu di akhir bulan dari 'start_date'
        tgl_jatuh_tempo_final = date(
            start_date.year, start_date.month, last_day_of_month
        )

    return LanggananCalculateResponse(
        harga_awal=round(harga_awal_final, 0), tgl_jatuh_tempo=tgl_jatuh_tempo_final
    )


# --- Endpoint untuk Import, Export, dan Template CSV ---


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

    response_headers = {
        "Content-Disposition": 'attachment; filename="template_import_langganan.csv"'
    }
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


@router.get("/export/csv", response_class=StreamingResponse)
async def export_to_csv_langganan(db: AsyncSession = Depends(get_db)):
    """Mengekspor semua data langganan ke dalam file CSV."""
    query = select(LanggananModel).options(
        selectinload(LanggananModel.pelanggan),
        selectinload(LanggananModel.paket_layanan),
    )
    result = await db.execute(query)
    langganan_list = result.scalars().unique().all()

    if not langganan_list:
        raise HTTPException(
            status_code=404, detail="Tidak ada data langganan untuk diekspor."
        )

    output = io.StringIO()
    output.write("\ufeff")
    rows_to_write = []
    for langganan in langganan_list:
        rows_to_write.append(
            {
                "Nama Pelanggan": (
                    langganan.pelanggan.nama if langganan.pelanggan else "N/A"
                ),
                "Email Pelanggan": (
                    langganan.pelanggan.email if langganan.pelanggan else "N/A"
                ),
                "Paket Layanan": (
                    langganan.paket_layanan.nama_paket
                    if langganan.paket_layanan
                    else "N/A"
                ),
                "Status": langganan.status,
                "Metode Pembayaran": langganan.metode_pembayaran,
                "Harga": langganan.harga_awal,
                "Tgl Jatuh Tempo": langganan.tgl_jatuh_tempo,
                "Tgl Invoice Terakhir": langganan.tgl_invoice_terakhir,
            }
        )

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


@router.post("/import/csv")
async def import_from_csv_langganan(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
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

    # --- OPTIMISASI: PRE-FETCH DATA SEBELUM LOOP (MENGHINDARI N+1 QUERY) ---
    emails_to_find = {row.get("email_pelanggan", "").lower().strip() for row in reader if row.get("email_pelanggan")}
    paket_names_to_find = {row.get("nama_paket_layanan", "").lower().strip() for row in reader if row.get("nama_paket_layanan")}
    brand_ids_to_find = {row.get("id_brand", "").strip() for row in reader if row.get("id_brand")}

    # 1. Ambil semua Pelanggan yang relevan dalam satu query
    pelanggan_q = await db.execute(select(PelangganModel).where(func.lower(PelangganModel.email).in_(emails_to_find)))
    pelanggan_map = {p.email.lower(): p for p in pelanggan_q.scalars().all()}

    # 2. Ambil semua Paket Layanan yang relevan dalam satu query
    paket_q = await db.execute(
        select(PaketLayananModel).where(
            func.lower(PaketLayananModel.nama_paket).in_(paket_names_to_find),
            PaketLayananModel.id_brand.in_(brand_ids_to_find)
        )
    )
    paket_map = {(p.nama_paket.lower(), p.id_brand): p for p in paket_q.scalars().all()}

    # 3. Ambil semua Langganan yang sudah ada untuk pelanggan yang ditemukan
    pelanggan_ids_found = [p.id for p in pelanggan_map.values()]
    existing_langganan_q = await db.execute(select(LanggananModel.pelanggan_id).where(LanggananModel.pelanggan_id.in_(pelanggan_ids_found)))
    subscribed_pelanggan_ids = set(existing_langganan_q.scalars().all())
    # --- AKHIR OPTIMISASI ---

    for row_num, row in enumerate(reader, start=2):
        try:
            data_import = LanggananImport(**row)

            # Lookup dari data yang sudah di-prefetch (tanpa query baru)
            pelanggan = pelanggan_map.get(data_import.email_pelanggan.lower())
            if not pelanggan:
                errors.append(
                    f"Baris {row_num}: Pelanggan dengan email '{data_import.email_pelanggan}' tidak ditemukan."
                )
                continue

            # Lookup paket menggunakan kunci gabungan (nama paket + brand)
            paket_key = (data_import.nama_paket_layanan.lower(), data_import.id_brand)
            paket = paket_map.get(paket_key)
            if not paket:
                errors.append(
                    f"Baris {row_num}: Paket Layanan '{data_import.nama_paket_layanan}' untuk brand '{data_import.id_brand}' tidak ditemukan."
                )
                continue

            # Cek langganan yang sudah ada dari data prefetch
            if pelanggan.id in subscribed_pelanggan_ids:
                errors.append(
                    f"Baris {row_num}: Pelanggan '{pelanggan.nama}' sudah memiliki langganan."
                )
                continue

            new_langganan_data = {
                "pelanggan_id": pelanggan.id,
                "paket_layanan_id": paket.id,
                "status": data_import.status,
                "metode_pembayaran": data_import.metode_pembayaran,
                "harga_awal": paket.harga,
                "tgl_jatuh_tempo": data_import.tgl_jatuh_tempo,
            }
            langganan_to_create.append(LanggananModel(**new_langganan_data))

        except ValidationError as e:
            error_messages = "; ".join(
                [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            )
            errors.append(f"Baris {row_num}: {error_messages}")
        except Exception as e:
            errors.append(f"Baris {row_num}: Terjadi error - {str(e)}")

    if errors:
        raise HTTPException(
            status_code=422,
            detail={"message": "Impor gagal, ditemukan error.", "errors": errors},
        )

    if not langganan_to_create:
        raise HTTPException(
            status_code=400, detail="Tidak ada data valid untuk diimpor."
        )

    try:
        db.add_all(langganan_to_create)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {e}")

    return {"message": f"Berhasil mengimpor {len(langganan_to_create)} langganan baru."}


# INVOICE GABUNGAN PRORATE + HARGA PAKET BUAT 2 BULAN


class LanggananCalculateProratePlusFullResponse(BaseModel):
    harga_prorate: float
    harga_normal: float
    harga_total_awal: float  # Total yang akan ditagihkan
    tgl_jatuh_tempo: date


@router.post(
    "/calculate-prorate-plus-full",
    response_model=LanggananCalculateProratePlusFullResponse,
)
async def calculate_langganan_price_plus_full(
    request_data: LanggananCalculateRequest, db: AsyncSession = Depends(get_db)
):
    """
    Menghitung harga gabungan: prorate bulan ini + harga penuh bulan depan.
    """
    pelanggan = await db.get(
        PelangganModel,
        request_data.pelanggan_id,
        options=[selectinload(PelangganModel.harga_layanan)],
    )
    if not pelanggan or not pelanggan.harga_layanan:
        raise HTTPException(
            status_code=404, detail="Data Brand pelanggan tidak ditemukan."
        )

    paket = await db.get(PaketLayananModel, request_data.paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan.")

    start_date = request_data.tgl_mulai
    harga_paket = float(paket.harga)
    pajak_persen = float(pelanggan.harga_layanan.pajak)

    # Hitung harga normal penuh untuk bulan depan
    harga_normal_full = harga_paket * (1 + (pajak_persen / 100))

    # Hitung harga prorate untuk sisa bulan ini
    _, last_day_of_month = monthrange(start_date.year, start_date.month)
    remaining_days = last_day_of_month - start_date.day + 1
    if remaining_days < 0:
        remaining_days = 0

    harga_per_hari = harga_paket / last_day_of_month
    prorated_price_before_tax = harga_per_hari * remaining_days
    harga_prorate_final = prorated_price_before_tax * (1 + (pajak_persen / 100))

    # Hitung total gabungan
    harga_total_final = harga_prorate_final + harga_normal_full

    # Jatuh tempo pembayaran pertama adalah di akhir bulan ini
    tgl_jatuh_tempo_final = date(start_date.year, start_date.month, last_day_of_month)

    return LanggananCalculateProratePlusFullResponse(
        harga_prorate=round(harga_prorate_final, 0),
        harga_normal=round(harga_normal_full, 0),
        harga_total_awal=round(harga_total_final, 0),
        tgl_jatuh_tempo=tgl_jatuh_tempo_final,
    )


@router.get("/pelanggan/list", response_model=List[PelangganSchema])
async def get_all_pelanggan_with_status(db: AsyncSession = Depends(get_db)):
    """
    Mengambil daftar semua pelanggan, dengan status langganan mereka.
    """
    # Gunakan LEFT JOIN untuk mendapatkan semua pelanggan, bahkan yang tidak punya langganan.
    result = await db.execute(
        select(PelangganModel)
        .options(selectinload(PelangganModel.langganan))
        .order_by(PelangganModel.nama)
    )
    pelanggan = result.scalars().unique().all()
    
    # Tambahkan atribut 'has_subscription' ke setiap objek pelanggan
    for p in pelanggan:
        p.has_subscription = len(p.langganan) > 0

    return pelanggan