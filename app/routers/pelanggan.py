import pandas as pd
from typing import List
import openpyxl
from io import BytesIO
from typing import Optional
from datetime import datetime, timedelta
import io
import csv
import chardet  # Add this import for encoding detection

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from dateutil import parser

from sqlalchemy import func, or_
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..websocket_manager import manager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import ValidationError
import logging

from ..models.pelanggan import Pelanggan as PelangganModel
from ..schemas.pelanggan import (
    Pelanggan as PelangganSchema,
    PelangganCreate,
    PelangganUpdate,
)
from ..database import get_db

router = APIRouter(
    prefix="/pelanggan",
    tags=["Pelanggan"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/", response_model=PelangganSchema, status_code=status.HTTP_201_CREATED)
async def create_pelanggan(
    pelanggan: PelangganCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat data pelanggan baru.
    """
    db_pelanggan = PelangganModel(**pelanggan.model_dump())
    db.add(db_pelanggan)
    await db.commit()
    # PERBAIKAN: Muat relasi secara eksplisit setelah membuat objek baru.
    # Ini mencegah error "MissingGreenlet" saat FastAPI mencoba mengakses relasi
    # yang belum di-load (lazy loading) di luar scope async.
    await db.refresh(db_pelanggan, attribute_names=["harga_layanan", "data_teknis"])

    try:
        # Cari semua user ID dengan role 'NOC' atau 'CS'
        target_roles = ["NOC", "CS", "Admin"]  # Sesuaikan nama role jika perlu
        query = (
            select(UserModel.id)
            .join(RoleModel)
            .where(func.lower(RoleModel.name).in_([r.lower() for r in target_roles]))
        )
        result = await db.execute(query)
        target_user_ids = result.scalars().all()

        if target_user_ids:
            # Siapkan payload notifikasi
            notification_payload = {
                "type": "new_customer_for_noc",
                "data": {
                    "pelanggan_id": db_pelanggan.id,
                    "pelanggan_nama": db_pelanggan.nama,
                    "message": f"Pelanggan baru '{db_pelanggan.nama}' telah ditambahkan. Segera buatkan Data Teknis.",
                },
            }
            # Kirim notifikasi ke user yang relevan
            await manager.broadcast_to_roles(notification_payload, target_user_ids)

    except Exception as e:
        # Jika pengiriman notifikasi gagal, jangan gagalkan proses utama
        logger.error(f"Gagal mengirim notifikasi pelanggan baru: {e}")

    return db_pelanggan


@router.get("/", response_model=List[PelangganSchema])
async def read_all_pelanggan(
    skip: int = 0,
    limit: Optional[int] = None,
    # Tambahkan parameter filter opsional di sini
    search: Optional[str] = None,
    alamat: Optional[str] = None,
    id_brand: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua pelanggan dengan paginasi dan filter.
    """
    # PERBAIKAN: Selalu muat relasi yang dibutuhkan oleh skema respons
    # menggunakan selectinload untuk menghindari error "MissingGreenlet"
    # akibat lazy loading.
    query = select(PelangganModel).options(
        selectinload(PelangganModel.data_teknis),
        selectinload(PelangganModel.harga_layanan),
    )

    # Terapkan filter pencarian umum (nama, email, no_telp)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                PelangganModel.nama.ilike(search_term),
                PelangganModel.email.ilike(search_term),
                PelangganModel.no_telp.ilike(search_term),
            )
        )

    # Terapkan filter berdasarkan alamat
    if alamat:
        query = query.where(PelangganModel.alamat == alamat)

    # Terapkan filter berdasarkan ID Brand
    if id_brand:
        query = query.where(PelangganModel.id_brand == id_brand)

    # Terapkan paginasi setelah semua filter
    if limit is not None:
        query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    pelanggan_list = result.scalars().all()
    return pelanggan_list


# ========== SEARCH OTOMATIS PAKET SESUAI =============#
@router.get("/{pelanggan_id}", response_model=PelangganSchema)
async def read_pelanggan_by_id(pelanggan_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mengambil satu data pelanggan spesifik berdasarkan ID-nya.
    """
    # PERBAIKAN: Ganti db.get() dengan select() untuk eager loading.
    # Ini mencegah error "MissingGreenlet" saat skema mencoba mengakses
    # relasi seperti 'harga_layanan' atau 'data_teknis'.
    query = (
        select(PelangganModel)
        .where(PelangganModel.id == pelanggan_id)
        .options(
            selectinload(PelangganModel.harga_layanan),
            selectinload(PelangganModel.data_teknis),
        )
    )
    result = await db.execute(query)
    db_pelanggan = result.scalar_one_or_none()

    if not db_pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan tidak ditemukan")
    return db_pelanggan


@router.patch("/{pelanggan_id}", response_model=PelangganSchema)
async def update_pelanggan(
    pelanggan_id: int,
    pelanggan_update: PelangganUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Memperbarui data pelanggan secara parsial (hanya field yang diisi).
    """
    # PERBAIKAN: Ganti db.get() dengan query select() agar bisa menggunakan
    # options(selectinload(...)) untuk eager loading relasi.
    query = (
        select(PelangganModel)
        .where(PelangganModel.id == pelanggan_id)
        .options(
            selectinload(PelangganModel.harga_layanan),
            selectinload(PelangganModel.data_teknis),
        )
    )
    result = await db.execute(query)
    db_pelanggan = result.scalar_one_or_none()

    if not db_pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan not found")

    update_data = pelanggan_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_pelanggan, key, value)

    db.add(db_pelanggan)
    await db.commit()
    await db.refresh(db_pelanggan, attribute_names=["harga_layanan", "data_teknis"])
    return db_pelanggan


@router.delete("/{pelanggan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pelanggan(pelanggan_id: int, db: AsyncSession = Depends(get_db)):
    """
    Menghapus data pelanggan berdasarkan ID.
    """
    db_pelanggan = await db.get(PelangganModel, pelanggan_id)
    if not db_pelanggan:
        raise HTTPException(status_code=404, detail="Pelanggan not found")

    await db.delete(db_pelanggan)
    await db.commit()
    return None


logger = logging.getLogger(__name__)


# ========================================================== IMPORT DAN EXPORT ==========================================================


@router.get("/template/csv", response_class=StreamingResponse)
async def download_csv_template():
    """
    Men-download template CSV sederhana untuk import pelanggan.
    """
    output = io.StringIO()

    # Menambahkan BOM (Byte Order Mark) agar file terbuka dengan benar di Excel
    output.write("\ufeff")

    # Header yang lebih sederhana, sesuai gambar kedua
    headers = [
        "Nama",
        "No KTP",
        "Email",
        "No Telepon",
        "Layanan",
        "Alamat",
        "Alamat 2",
        "Blok",
        "Unit",
        "Tanggal Instalasi (YYYY-MM-DD)",
        "ID Brand",
    ]

    # Data contoh yang lebih ringkas
    sample_data = [
        {
            "Nama": "John Doe",
            "No KTP": "1234567890123456",
            "Email": "john.doe@example.com",
            "No Telepon": "081234567890",
            "Layanan": "Internet 50 Mbps",
            "Alamat": "Jl. Contoh No 01",
            "Alamat 2": "RT 01 RW A",
            "Blok": "A",
            "Unit": "12",
            "Tanggal Instalasi (YYYY-MM-DD)": "2024-01-15",
            "ID Brand": "ajn-01",
        },
        {
            "Nama": "Jane Smith",
            "No KTP": "9876543210987654",
            "Email": "jane.smith@example.com",
            "No Telepon": "085987654321",
            "Layanan": "Internet 20 Mbps",
            "Alamat": "Jl. Sample Stn R7 01",
            "Alamat 2": "RW B",
            "Blok": "B",
            "Unit": "25",
            "Tanggal Instalasi (YYYY-MM-DD)": "2024-02-20",
            "ID Brand": "ajn-02",
        },
    ]

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample_data)

    output.seek(0)

    # Mengatur nama file saat di-download
    response_headers = {
        "Content-Disposition": 'attachment; filename="template_import_pelanggan.csv"'
    }

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# --- FUNGSI BARU: EXPORT DATA KE CSV ---
@router.get("/export/csv", response_class=StreamingResponse)
async def export_to_csv(db: AsyncSession = Depends(get_db)):
    """
    Mengekspor semua data pelanggan ke dalam file CSV.
    """
    query = select(PelangganModel)
    result = await db.execute(query)
    pelanggan_list = result.scalars().all()

    if not pelanggan_list:
        raise HTTPException(
            status_code=404, detail="Tidak ada data pelanggan untuk diekspor."
        )

    output = io.StringIO()
    output.write("\ufeff")  # BOM for Excel compatibility

    # Ambil header dari field model pertama
    headers = pelanggan_list[0].to_dict().keys()
    writer = csv.DictWriter(output, fieldnames=headers)

    writer.writeheader()
    for pelanggan in pelanggan_list:
        writer.writerow(pelanggan.to_dict())

    output.seek(0)

    filename = f"export_pelanggan_{datetime.now().strftime('%Y%m%d')}.csv"
    response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


# --- FUNGSI BARU: IMPORT DATA DARI CSV (SANGAT ROBUST) ---
@router.post("/import")
async def import_from_csv(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """
    Mengimpor data pelanggan dari file CSV dengan validasi mendalam dan laporan error.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File kosong.")

    try:
        encoding = chardet.detect(contents)["encoding"] or "utf-8"
        content_str = contents.decode(encoding)
        stream = io.StringIO(content_str)
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="Header CSV tidak ditemukan.")
    except Exception as e:
        logger.error(f"Gagal membaca atau mem-parsing file CSV: {repr(e)}")
        raise HTTPException(
            status_code=400, detail=f"Gagal memproses file CSV: {repr(e)}"
        )

    column_mapping = {
        "Nama": "nama",
        "No KTP": "no_ktp",
        "Email": "email",
        "No Telepon": "no_telp",
        "Alamat": "alamat",
        "Alamat 2": "alamat_2",
        "Blok": "blok",
        "Unit": "unit",
        "Tanggal Instalasi (YYYY-MM-DD)": "tgl_instalasi",
        "Layanan": "layanan",
        "ID Brand": "id_brand",
    }

    new_customers = []
    errors = []
    processed_emails_in_file = set()

    # Ambil semua email yang ada di database dalam satu query untuk efisiensi
    existing_emails_q = await db.execute(select(func.lower(PelangganModel.email)))
    existing_emails_in_db = set(existing_emails_q.scalars().all())

    for row_num, row in enumerate(reader, start=2):
        data = {
            # PERBAIKAN: Hapus kondisi `if` agar semua kolom diproses.
            # Ini memungkinkan Pydantic melakukan validasi yang benar untuk field kosong.
            model_field: row.get(csv_header, "").strip()
            for csv_header, model_field in column_mapping.items()
        }
        if not data:
            continue

        try:
            # Validasi dan konversi tanggal
            tgl_instalasi_str = data.get("tgl_instalasi")
            if tgl_instalasi_str:
                try:
                    data["tgl_instalasi"] = parser.parse(tgl_instalasi_str).date()
                except (parser.ParserError, ValueError):
                    errors.append(
                        f"Baris {row_num}: Format tanggal tidak valid untuk '{tgl_instalasi_str}'. Gunakan YYYY-MM-DD."
                    )
                    continue
            else:
                data["tgl_instalasi"] = None

            # Validasi format Pydantic
            customer_schema = PelangganCreate(**data)
            email_lower = customer_schema.email.lower()

            # Validasi duplikat di file CSV
            if email_lower in processed_emails_in_file:
                errors.append(
                    f"Baris {row_num}: Email '{customer_schema.email}' duplikat di dalam file CSV."
                )
                continue

            # Validasi duplikat di database
            if email_lower in existing_emails_in_db:
                errors.append(
                    f"Baris {row_num}: Email '{customer_schema.email}' sudah terdaftar di database."
                )
                continue

            new_customers.append(PelangganModel(**customer_schema.model_dump()))
            processed_emails_in_file.add(email_lower)
            logger.info(
                f"Valid customer prepared from row {row_num}: {data.get('nama')}"
            )

        except ValidationError as e:
            error_details = "; ".join(
                [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            )
            errors.append(f"Baris {row_num}: {error_details}")
        except Exception as e:
            # Gunakan repr(e) untuk penanganan error yang aman
            errors.append(f"Baris {row_num}: Terjadi error tak terduga - {repr(e)}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": f"Ditemukan {len(errors)} kesalahan dalam file.",
                "errors": errors,
            },
        )

    if not new_customers:
        raise HTTPException(
            status_code=400, detail="Tidak ada data pelanggan yang valid untuk diimpor."
        )

    try:
        db.add_all(new_customers)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during import: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Gagal menyimpan ke database: {repr(e)}"
        )

    return {
        "message": f"Sukses! Berhasil mengimpor {len(new_customers)} pelanggan baru."
    }


# ========================================================== IMPORT DAN EXPORT ==========================================================


@router.get("/lokasi/unik", response_model=List[str])
async def get_unique_lokasi(db: AsyncSession = Depends(get_db)):
    """
    Mengambil daftar semua alamat/lokasi pelanggan yang unik dari database.
    """
    query = select(PelangganModel.alamat).distinct().order_by(PelangganModel.alamat)
    result = await db.execute(query)
    lokasi_list = result.scalars().all()
    # Filter None atau string kosong jika ada
    return [lokasi for lokasi in lokasi_list if lokasi]
