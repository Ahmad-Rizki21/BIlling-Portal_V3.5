import csv
import io
import logging
from collections import Counter
from datetime import datetime
from io import BytesIO
from typing import List, Optional

import chardet
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database import AsyncSessionLocal

# Impor model DataTeknis
from ..models.data_teknis import DataTeknis as DataTeknisModel
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..models.odp import ODP as ODPModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel

# Impor model Pelanggan dengan nama asli 'Pelanggan', lalu kita beri alias 'PelangganModel'
from ..models.pelanggan import Pelanggan as PelangganModel
from ..models.role import Role as RoleModel
from ..models.user import User as UserModel

# Impor semua skema yang dibutuhkan
from ..schemas.data_teknis import DataTeknis as DataTeknisSchema
from ..schemas.data_teknis import (
    DataTeknisCreate,
    DataTeknisImport,
    DataTeknisUpdate,
    IPCheckRequest,
    IPCheckResponse,
)
from ..services import mikrotik_service
from ..websocket_manager import manager

# --- PASTIKAN SEMUA IMPORT INI ADA DAN BENAR ---







class ProfileUsage(BaseModel):
    profile_name: str
    usage_count: int


# Impor database session
from ..database import get_db

router = APIRouter(
    prefix="/data_teknis",
    tags=["Data Teknis"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)


@router.post("/", response_model=DataTeknisSchema, status_code=status.HTTP_201_CREATED)
async def create_data_teknis(data_teknis: DataTeknisCreate, db: AsyncSession = Depends(get_db)):
    """
    Membuat data teknis baru untuk seorang pelanggan.
    """
    # Validasi: Pastikan pelanggan dengan ID yang diberikan ada
    pelanggan = await db.get(PelangganModel, data_teknis.pelanggan_id)
    if not pelanggan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pelanggan dengan id {data_teknis.pelanggan_id} tidak ditemukan.",
        )

    # Cek apakah pelanggan ini sudah punya data teknis
    existing_data_teknis_query = await db.execute(
        select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == data_teknis.pelanggan_id)
    )
    if existing_data_teknis_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Data teknis untuk pelanggan dengan id {data_teknis.pelanggan_id} sudah ada.",
        )

    db_data_teknis = DataTeknisModel(**data_teknis.model_dump())
    db.add(db_data_teknis)
    await db.commit()
    await db.refresh(db_data_teknis, attribute_names=["pelanggan"])  # Eager load pelanggan

    try:
        # 1. Cari semua user ID dengan role "Finance"
        finance_role_query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name) == "Finance")
        result = await db.execute(finance_role_query)
        finance_user_ids = result.scalars().all()

        if finance_user_ids:
            # 2. Siapkan payload notifikasi
            notification_payload = {
                "type": "new_technical_data",
                "data": {
                    "pelanggan_id": db_data_teknis.pelanggan_id,  # <-- TAMBAHKAN BARIS INI
                    "pelanggan_nama": (db_data_teknis.pelanggan.nama if db_data_teknis.pelanggan else "N/A"),
                    "message": f"Data teknis untuk {db_data_teknis.pelanggan.nama} telah ditambahkan. Siap dibuatkan langganan.",
                },
            }
            # 3. Kirim notifikasi ke semua user Finance yang online
            await manager.broadcast_to_roles(notification_payload, finance_user_ids)
            logger.info(f"Notifikasi data teknis baru dikirim ke {len(finance_user_ids)} user Finance.")
    except Exception as e:
        logger.error(f"Gagal mengirim notifikasi data teknis baru: {str(e)}")

    try:
        # Panggil fungsi trigger setelah data berhasil disimpan
        await mikrotik_service.trigger_mikrotik_create(db, db_data_teknis)
    except Exception as e:
        # Jika gagal membuat secret, jangan batalkan proses.
        # Cukup catat errornya. Data teknis tetap berhasil dibuat.
        logger.error(f"Data teknis ID {db_data_teknis.id} berhasil disimpan, " f"namun gagal membuat secret di Mikrotik: {e}")

    return db_data_teknis


@router.get("/", response_model=List[DataTeknisSchema])
async def read_all_data_teknis(
    skip: int = 0,
    limit: Optional[int] = None,
    search: Optional[str] = None,
    olt: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua data teknis dengan paginasi dan filter.
    """
    query = select(DataTeknisModel).options(selectinload(DataTeknisModel.pelanggan))

    if search:
        search_term = f"%{search}%"
        query = query.join(PelangganModel, DataTeknisModel.pelanggan_id == PelangganModel.id).where(
            or_(
                func.coalesce(PelangganModel.nama, "").ilike(search_term),
                func.coalesce(DataTeknisModel.id_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.ip_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.sn, "").ilike(search_term),
            )
        )
    else:
        # Jika tidak ada pencarian, tetap gunakan join biasa agar data pelanggan ter-load
        query = query.join(DataTeknisModel.pelanggan)

    if olt:
        query = query.where(DataTeknisModel.olt == olt)

    if limit is not None:
        query = query.offset(skip).limit(limit)

    result = await db.execute(query)

    # --- PERBAIKAN DI SINI ---
    # Ubah urutan menjadi .unique().scalars().all()
    data_teknis_list = result.unique().scalars().all()

    return data_teknis_list


@router.get("/{data_teknis_id}", response_model=DataTeknisSchema)
async def read_data_teknis_by_id(data_teknis_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mengambil satu data teknis berdasarkan ID.
    """
    db_data_teknis = await db.get(DataTeknisModel, data_teknis_id)
    if db_data_teknis is None:
        raise HTTPException(status_code=404, detail="Data Teknis not found")
    return db_data_teknis


@router.patch("/{data_teknis_id}", response_model=DataTeknisSchema)
async def update_data_teknis(
    data_teknis_id: int,
    data_teknis_update: DataTeknisUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Memperbarui data teknis secara parsial DAN mentrigger update ke Mikrotik.
    """
    db_data_teknis = await db.get(
        DataTeknisModel,
        data_teknis_id,
        options=[selectinload(DataTeknisModel.pelanggan).selectinload(PelangganModel.langganan)],
    )
    if not db_data_teknis:
        raise HTTPException(status_code=404, detail="Data Teknis not found")

    # ▼▼▼ PERUBAHAN DI SINI ▼▼▼
    # Simpan ID Pelanggan (nama secret) LAMA sebelum diubah
    old_id_pelanggan = db_data_teknis.id_pelanggan

    # Perbarui data di objek SQLAlchemy
    update_data = data_teknis_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_data_teknis, key, value)

    # Simpan perubahan ke database
    db.add(db_data_teknis)
    await db.commit()
    await db.refresh(db_data_teknis)

    try:
        if db_data_teknis.pelanggan and db_data_teknis.pelanggan.langganan:
            langganan_terkait = db_data_teknis.pelanggan.langganan[0]

            logger.info(f"Mentrigger update Mikrotik untuk Data Teknis ID: {db_data_teknis.id}")
            # Panggil service dengan argumen baru: nama lama
            await mikrotik_service.trigger_mikrotik_update(db, langganan_terkait, db_data_teknis, old_id_pelanggan)
        else:
            logger.warning(
                f"Data Teknis ID {db_data_teknis.id} diupdate, "
                f"tapi tidak ada langganan terkait untuk trigger update Mikrotik."
            )
    except Exception as e:
        logger.error(
            f"Data teknis ID {db_data_teknis.id} berhasil diupdate di DB, " f"namun GAGAL sinkronisasi ke Mikrotik: {e}"
        )

    return db_data_teknis


@router.delete("/{data_teknis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_teknis(data_teknis_id: int, db: AsyncSession = Depends(get_db)):
    """
    Menghapus data teknis berdasarkan ID.
    """
    db_data_teknis = await db.get(DataTeknisModel, data_teknis_id)
    if not db_data_teknis:
        raise HTTPException(status_code=404, detail="Data Teknis not found")

    await db.delete(db_data_teknis)
    await db.commit()
    return None


# Validasi IP
@router.post("/check-ip", response_model=IPCheckResponse)
async def check_ip_address(request: IPCheckRequest, db: AsyncSession = Depends(get_db)):
    # 1. Pengecekan ke database (tetap sama)
    query = select(DataTeknisModel).where(DataTeknisModel.ip_pelanggan == request.ip_address)
    if request.current_id:
        query = query.where(DataTeknisModel.id != request.current_id)

    existing_in_db = (await db.execute(query)).scalar_one_or_none()

    if existing_in_db:
        return IPCheckResponse(
            is_taken=True,
            message=f"IP sudah terpakai di database oleh {existing_in_db.id_pelanggan}",
            owner_id=existing_in_db.id_pelanggan,
        )

    # 2. Jika tidak ditemukan di DB, cek ke semua server Mikrotik
    mikrotik_servers_result = await db.execute(select(MikrotikServerModel))
    all_servers = mikrotik_servers_result.scalars().all()

    for server in all_servers:
        api, connection = mikrotik_service.get_api_connection(server)
        if api:
            try:
                owner_name = mikrotik_service.check_ip_in_secrets(api, request.ip_address)
                if owner_name:
                    return IPCheckResponse(
                        is_taken=True,
                        message=f"IP sudah terpakai di Mikrotik '{server.name}' oleh {owner_name}",
                        owner_id=owner_name,
                    )
            finally:
                if connection:
                    connection.disconnect()

    # 3. Jika aman di DB dan di semua Mikrotik, maka IP tersedia
    return IPCheckResponse(is_taken=False, message="IP tersedia", owner_id=None)


# routers/data_teknis.py

# ==========================================================
# FUNGSI DOWNLOAD DAN IMPORT, EXPORT CSV FILE
# ==========================================================


@router.get("/template/csv", response_class=StreamingResponse)
async def download_csv_template_teknis():
    """
    Men-download template CSV untuk import data teknis yang telah disesuaikan
    dengan model baru (menggunakan nama, bukan ID).
    """
    output = io.StringIO()
    output.write("\ufeff")  # BOM untuk Excel

    # --- HEADER DISESUAIKAN DENGAN SKEMA IMPORT BARU ---
    headers = [
        "email_pelanggan",
        "olt",  # KEMBALIKAN menjadi 'olt' agar sesuai dengan file Anda
        "kode_odp",
        "port_odp",
        "id_vlan",
        "id_pelanggan",
        "password_pppoe",
        "ip_pelanggan",
        "profile_pppoe",
        "olt_custom",
        "pon",
        "otb",
        "odc",
        "onu_power",
        "sn",
    ]

    sample_data = [
        {
            "email_pelanggan": "budi.s@example.com",
            "olt": "Mikrotik-Pusat",  # CONTOH NAMA
            "kode_odp": "ODP-TMB-01",  # CONTOH KODE
            "port_odp": 1,  # CONTOH PORT
            "id_vlan": "101",
            "id_pelanggan": "budi-santoso",
            "password_pppoe": "pass123",
            "ip_pelanggan": "10.10.1.25",
            "profile_pppoe": "50mbps-profile",
            "olt_custom": "OLT-Tambun-Satu",
            "pon": 1,
            "otb": 1,
            "odc": 3,
            "onu_power": -22,
            "sn": "ZTEG1A2B3C4D",
        }
    ]

    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(sample_data)
    output.seek(0)

    response_headers = {"Content-Disposition": 'attachment; filename="template_import_teknis.csv"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


@router.get("/export/csv", response_class=StreamingResponse)
async def export_to_csv_teknis(db: AsyncSession = Depends(get_db)):
    """
    Mengekspor data teknis ke CSV dengan data relasi yang mudah dibaca.
    """
    # --- QUERY DIPERBARUI untuk Eager Load relasi baru ---
    query = select(DataTeknisModel).options(
        selectinload(DataTeknisModel.pelanggan),
        selectinload(DataTeknisModel.mikrotik_server),
        selectinload(DataTeknisModel.odp),  # BARU: Eager load data ODP
    )
    result = await db.execute(query)
    data_list = result.scalars().unique().all()

    if not data_list:
        raise HTTPException(status_code=404, detail="Tidak ada data teknis untuk diekspor.")

    output = io.StringIO()
    output.write("\ufeff")

    rows_to_write = []
    for d in data_list:
        rows_to_write.append(
            {
                "Nama Pelanggan": d.pelanggan.nama if d.pelanggan else "N/A",
                "Email Pelanggan": d.pelanggan.email if d.pelanggan else "N/A",
                "ID Pelanggan (PPPoE)": d.id_pelanggan,
                "IP Pelanggan": d.ip_pelanggan,
                "Profile PPPoE": d.profile_pppoe,
                "VLAN": d.id_vlan,
                # DIUBAH: Tampilkan nama server, bukan ID
                "Nama Mikrotik Server": (d.mikrotik_server.name if d.mikrotik_server else "N/A"),
                # DIUBAH: Tampilkan kode ODP, bukan ID
                "Kode ODP": d.odp.kode_odp if d.odp else "N/A",
                "Port ODP": d.port_odp,  # BARU
                "OLT Custom": d.olt_custom,
                "PON": d.pon,
                "OTB": d.otb,
                "ODC": d.odc,
                "ONU Power (dBm)": d.onu_power,
                "Serial Number": d.sn,
            }
        )

    if not rows_to_write:
        raise HTTPException(status_code=404, detail="Tidak ada data valid untuk diekspor.")

    writer = csv.DictWriter(output, fieldnames=rows_to_write[0].keys())
    writer.writeheader()
    writer.writerows(rows_to_write)
    output.seek(0)

    filename = f"export_data_teknis_{datetime.now().strftime('%Y%m%d')}.csv"
    response_headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )


@router.post("/import/csv")
async def import_from_csv_teknis(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Mengimpor data teknis dari file CSV dengan validasi relasi berdasarkan nama/kode.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat .csv")

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File kosong.")

    try:
        encoding = chardet.detect(contents)["encoding"] or "utf-8"
        content_str = contents.decode(encoding)

        # --- PERBAIKAN DI SINI ---
        # 1. Buat objek DictReader terlebih dahulu
        reader_object = csv.DictReader(io.StringIO(content_str))

        # 2. Cek 'fieldnames' pada objek DictReader, BUKAN pada list
        if not reader_object.fieldnames:
            raise HTTPException(status_code=400, detail="Header CSV tidak ditemukan.")
        # 3. SEKARANG baru ubah menjadi list untuk di-loop
        reader = list(reader_object)
    except Exception as e:
        logger.error(f"Gagal membaca atau mem-parsing file CSV: {repr(e)}")
        raise HTTPException(status_code=400, detail=f"Gagal memproses file CSV: {repr(e)}")

    # --- OPTIMISASI: PRE-FETCH DATA SEBELUM LOOP (MENGHINDARI N+1 QUERY) ---
    # 1. Kumpulkan semua data unik yang perlu dicari dari CSV
    emails_to_find = {row.get("email_pelanggan", "").lower().strip() for row in reader if row.get("email_pelanggan")}
    server_names_to_find = {row.get("olt", "").strip() for row in reader if row.get("olt")}
    odp_codes_to_find = {row.get("kode_odp", "").strip() for row in reader if row.get("kode_odp")}

    # 2. Lakukan query besar-besaran di luar loop untuk efisiensi
    # Ambil semua pelanggan yang relevan dalam satu query
    pelanggan_q = await db.execute(select(PelangganModel).where(func.lower(PelangganModel.email).in_(emails_to_find)))
    pelanggan_map = {p.email.lower(): p for p in pelanggan_q.scalars().all()}

    # Ambil semua server yang relevan dalam satu query
    server_q = await db.execute(select(MikrotikServerModel).where(MikrotikServerModel.name.in_(server_names_to_find)))
    server_map = {s.name: s for s in server_q.scalars().all()}

    # Ambil semua ODP yang relevan dalam satu query
    odp_q = await db.execute(select(ODPModel).where(ODPModel.kode_odp.in_(odp_codes_to_find)))
    odp_map = {o.kode_odp: o for o in odp_q.scalars().all()}

    # Ambil semua data teknis yang sudah ada untuk pelanggan yang ditemukan
    pelanggan_ids_found = [p.id for p in pelanggan_map.values()]
    existing_teknis_q = await db.execute(
        select(DataTeknisModel.pelanggan_id).where(DataTeknisModel.pelanggan_id.in_(pelanggan_ids_found))
    )
    existing_teknis_pelanggan_ids = set(existing_teknis_q.scalars().all())
    # --- AKHIR OPTIMISASI ---

    errors = []
    data_to_create = []
    processed_emails = set()

    for row_num, row in enumerate(reader, start=2):
        try:
            # 1. Validasi format baris menggunakan Pydantic dengan alias 'olt'
            data_import = DataTeknisImport.model_validate(row)
            email = data_import.email_pelanggan.lower().strip()

            # 2. Validasi dari data yang sudah di-prefetch (tanpa query baru)
            pelanggan = pelanggan_map.get(email)
            if not pelanggan:
                errors.append(f"Baris {row_num}: Pelanggan dengan email '{email}' tidak ditemukan.")
                continue

            # Cek duplikasi email di file & apakah pelanggan sudah punya data teknis
            if email in processed_emails:
                errors.append(f"Baris {row_num}: Email '{email}' duplikat di dalam file.")
                continue
            if pelanggan.id in existing_teknis_pelanggan_ids:
                errors.append(f"Baris {row_num}: Pelanggan '{pelanggan.nama}' sudah memiliki data teknis.")
                continue

            # 3. Validasi Relasi ke Mikrotik Server (OLT)
            mikrotik_server = server_map.get(data_import.nama_mikrotik_server)
            if not mikrotik_server:
                errors.append(
                    f"Baris {row_num}: OLT/Mikrotik Server dengan nama '{data_import.nama_mikrotik_server}' tidak ditemukan."
                )
                continue

            # 4. Validasi Relasi ke ODP (jika diisi)
            odp_id = None
            if data_import.kode_odp:
                odp = odp_map.get(data_import.kode_odp)
                if not odp:
                    errors.append(f"Baris {row_num}: ODP dengan kode '{data_import.kode_odp}' tidak ditemukan.")
                    continue
                odp_id = odp.id

            # 5. Siapkan data untuk disimpan ke database
            teknis_data_dict = data_import.model_dump(exclude={"email_pelanggan", "nama_mikrotik_server", "kode_odp"})

            teknis_data_dict["pelanggan_id"] = pelanggan.id
            teknis_data_dict["mikrotik_server_id"] = mikrotik_server.id
            teknis_data_dict["odp_id"] = odp_id

            # INI BAGIAN PENTING: Simpan NAMA server ke kolom 'olt' untuk ditampilkan
            teknis_data_dict["olt"] = mikrotik_server.name

            data_to_create.append(DataTeknisModel(**teknis_data_dict))
            processed_emails.add(email)

        except ValidationError as e:
            error_details = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()])
            errors.append(f"Baris {row_num}: {error_details}")
        except Exception as e:
            errors.append(f"Baris {row_num}: Terjadi error tak terduga - {repr(e)}")

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": f"Ditemukan {len(errors)} kesalahan.", "errors": errors},
        )

    if not data_to_create:
        raise HTTPException(status_code=400, detail="Tidak ada data valid untuk diimpor.")

    try:
        db.add_all(data_to_create)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Database error during import: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan ke database: {repr(e)}")

    return {"message": f"Berhasil mengimpor {len(data_to_create)} data teknis baru."}


# ==========================================================
# FUNGSI DOWNLOAD DAN IMPORT, EXPORT CSV FILE
# ==========================================================


@router.get(
    "/available-profiles/{paket_layanan_id}/{pelanggan_id}",
    response_model=List[ProfileUsage],
)
async def get_available_profiles(
    paket_layanan_id: int,
    pelanggan_id: int,
    mikrotik_server_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Menyediakan daftar PPPoE profile yang relevan.
    Logika ini cerdas:
    1. Saat EDIT, ia akan menggunakan server yang sudah tersimpan di data teknis.
    2. Saat CREATE, ia akan menggunakan server yang dipilih di form (dikirim via query param).
    """
    # 1. Ambil paket layanan (tidak berubah)
    paket = await db.get(PaketLayananModel, paket_layanan_id)
    if not paket:
        raise HTTPException(status_code=404, detail="Paket Layanan tidak ditemukan")

    # 2. Coba cari Data Teknis yang sudah ada untuk pelanggan ini (untuk mode EDIT)
    data_teknis_stmt = select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == pelanggan_id)
    data_teknis = (await db.execute(data_teknis_stmt)).scalar_one_or_none()

    # 3. Tentukan ID server yang akan digunakan
    server_id_to_use = None
    if data_teknis and data_teknis.mikrotik_server_id:
        # Prioritas 1: Gunakan ID dari data teknis yang sudah ada (mode EDIT)
        server_id_to_use = data_teknis.mikrotik_server_id
        logger.info(f"Mode Edit: Menggunakan server ID {server_id_to_use} dari database.")
    elif mikrotik_server_id:
        # Prioritas 2: Gunakan ID dari query param (mode CREATE)
        server_id_to_use = mikrotik_server_id
        logger.info(f"Mode Create: Menggunakan server ID {server_id_to_use} dari form.")
    else:
        # Jika tidak ada data teknis DAN tidak ada ID dari form, kita tidak bisa lanjut.
        logger.warning(
            f"Tidak dapat menentukan server Mikrotik untuk pelanggan ID {pelanggan_id}. Data teknis tidak ada dan mikrotik_server_id tidak diberikan."
        )
        return []

    # 4. Ambil info server Mikrotik berdasarkan ID yang sudah ditentukan
    mikrotik_server_info = await db.get(MikrotikServerModel, server_id_to_use)
    if not mikrotik_server_info:
        logger.error(f"Server Mikrotik dengan ID {server_id_to_use} tidak ditemukan di database.")
        raise HTTPException(
            status_code=404,
            detail=f"Server Mikrotik untuk pelanggan ini tidak ditemukan.",
        )

    # --- Logika selanjutnya sama, tapi sekarang menggunakan server yang PASTI BENAR ---
    kecepatan_str = f"{paket.kecepatan}Mbps"

    api, connection = mikrotik_service.get_api_connection(mikrotik_server_info)
    if not api:
        raise HTTPException(
            status_code=503,
            detail=f"Tidak dapat terhubung ke server Mikrotik {mikrotik_server_info.name}",
        )

    try:
        all_profiles_on_router = mikrotik_service.get_all_ppp_profiles(api)
        relevant_profiles = [p for p in all_profiles_on_router if kecepatan_str in p]

        if not relevant_profiles:
            logger.info(f"Tidak ada profile dengan '{kecepatan_str}' ditemukan di Mikrotik.")
            return []

        active_connections = mikrotik_service.get_active_connections(api)
        active_profile_names = [conn.get("profile") for conn in active_connections if "profile" in conn]
        profile_usage_map = Counter(active_profile_names)

        response_data = []
        for profile_name in relevant_profiles:
            response_data.append(
                ProfileUsage(
                    profile_name=profile_name,
                    usage_count=profile_usage_map.get(profile_name, 0),
                )
            )

        response_data.sort(key=lambda x: x.profile_name)
        return response_data

    except Exception as e:
        logger.error(f"Terjadi error saat mengambil data profile dari Mikrotik: {e}")
        raise HTTPException(status_code=500, detail="Gagal memproses data dari Mikrotik.")
    finally:
        if connection:
            logger.info("Menutup koneksi Mikrotik.")
            connection.disconnect()


# Perbarui endpoint lama untuk menjaga kompatibilitas, tapi berikan peringatan
@router.get(
    "/available-profiles/{paket_layanan_id}",
    response_model=List[ProfileUsage],
    include_in_schema=False,
)
async def get_available_profiles_legacy(paket_layanan_id: int, db: AsyncSession = Depends(get_db)):
    """Fungsi lama, gunakan yang baru dengan pelanggan_id."""
    logger.warning("Memanggil endpoint lama /available-profiles/{paket_layanan_id}. Gunakan yang baru.")
    # Fallback ke server aktif pertama
    server_result = await db.execute(select(MikrotikServerModel).where(MikrotikServerModel.is_active == True))
    server_to_check = server_result.scalars().first()

    if not server_to_check:
        return []

    # Lanjutkan logika yang sama seperti di fungsi utama, tetapi tanpa pelanggan_id
    paket = await db.get(PaketLayananModel, paket_layanan_id)
    if not paket:
        return []

    kecepatan_str = f"{paket.kecepatan}Mbps"
    api, connection = mikrotik_service.get_api_connection(server_to_check)
    if not api:
        raise HTTPException(status_code=503, detail="Tidak dapat terhubung ke Mikrotik.")

    try:
        all_profiles_on_router = mikrotik_service.get_all_ppp_profiles(api)
        relevant_profiles = [p for p in all_profiles_on_router if kecepatan_str in p]

        active_connections = mikrotik_service.get_active_connections(api)
        active_profile_names = [conn.get("profile") for conn in active_connections if "profile" in conn]

        profile_usage_map = Counter(active_profile_names)

        response_data = []
        for profile_name in relevant_profiles:
            response_data.append(
                ProfileUsage(
                    profile_name=profile_name,
                    usage_count=profile_usage_map.get(profile_name, 0),
                )
            )

        response_data.sort(key=lambda x: x.profile_name)
        return response_data
    finally:
        if connection:
            connection.disconnect()
