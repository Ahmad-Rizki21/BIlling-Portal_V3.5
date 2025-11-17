from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, or_
from sqlalchemy.future import select
from typing import List, Optional
import csv
import io
from datetime import datetime, date
import chardet
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import joinedload
import logging
from io import BytesIO
from collections import Counter
from fastapi.responses import StreamingResponse
import uuid

# --- PASTIKAN SEMUA IMPORT INI ADA DAN BENAR ---

# Impor model Pelanggan dengan nama asli 'Pelanggan', lalu kita beri alias 'PelangganModel'
from ..models.pelanggan import Pelanggan as PelangganModel
from ..database import AsyncSessionLocal
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..models.paket_layanan import PaketLayanan as PaketLayananModel

from ..services import mikrotik_service

from ..websocket_manager import manager
from ..models.user import User as UserModel
from ..models.role import Role as RoleModel
from ..models.odp import ODP as ODPModel

# Impor model DataTeknis
from ..models.data_teknis import DataTeknis as DataTeknisModel

# Impor semua skema yang dibutuhkan
from ..schemas.data_teknis import (
    DataTeknis as DataTeknisSchema,
    DataTeknisCreate,
    DataTeknisUpdate,
    DataTeknisImport,
    IPCheckRequest,  # <-- Import dari data_teknis.py, bukan pelanggan.py
    IPCheckResponse,
)


class ProfileUsage(BaseModel):
    profile_name: str
    usage_count: int


class DataTeknisResponse(BaseModel):
    data: List[DataTeknisSchema]
    total_count: int


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
    # Pisahkan ID relasi dari data utama
    data_dict = data_teknis.model_dump()
    pelanggan_id = data_dict.pop("pelanggan_id")
    mikrotik_server_id = data_dict.pop("mikrotik_server_id", None)
    odp_id = data_dict.pop("odp_id", None)
    data_dict.pop("odp", None)  # Secara eksplisit hapus field 'odp' yang salah

    # Validasi: Pastikan pelanggan dengan ID yang diberikan ada
    pelanggan = await db.get(PelangganModel, pelanggan_id)
    if not pelanggan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pelanggan dengan id {pelanggan_id} tidak ditemukan.",
        )

    # Cek apakah pelanggan ini sudah punya data teknis
    existing_data_teknis_query = await db.execute(select(DataTeknisModel).where(DataTeknisModel.pelanggan_id == pelanggan_id))
    if existing_data_teknis_query.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Data teknis untuk pelanggan dengan id {pelanggan_id} sudah ada.",
        )

    # Buat instance model dengan data non-relasi
    db_data_teknis = DataTeknisModel(**data_dict)

    # Tetapkan relasi menggunakan objek yang diambil dari DB
    db_data_teknis.pelanggan = pelanggan

    if mikrotik_server_id:
        mikrotik_server = await db.get(MikrotikServerModel, mikrotik_server_id)
        if not mikrotik_server:
            raise HTTPException(
                status_code=404,
                detail=f"Server Mikrotik dengan id {mikrotik_server_id} tidak ditemukan.",
            )
        db_data_teknis.mikrotik_server = mikrotik_server

    if odp_id:
        odp = await db.get(ODPModel, odp_id)
        if not odp:
            raise HTTPException(status_code=404, detail=f"ODP dengan id {odp_id} tidak ditemukan.")
        db_data_teknis.odp = odp
    db.add(db_data_teknis)
    await db.commit()
    await db.refresh(db_data_teknis, attribute_names=["pelanggan"])  # Eager load pelanggan

    try:
        # 1. Cari semua user ID dengan role "Finance"
        finance_role_query = select(UserModel.id).join(RoleModel).where(func.lower(RoleModel.name) == "Finance")
        result = await db.execute(finance_role_query)
        finance_user_ids = list(result.scalars().all())

        if finance_user_ids:
            # 2. Siapkan payload notifikasi dengan format yang konsisten
            pelanggan_nama = db_data_teknis.pelanggan.nama if db_data_teknis.pelanggan else "N/A"
            notification_payload = {
                "type": "new_technical_data",
                "message": f"Data teknis untuk {pelanggan_nama} telah ditambahkan. Siap dibuatkan langganan.",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "pelanggan_id": db_data_teknis.pelanggan_id,
                    "pelanggan_nama": pelanggan_nama,
                    "timestamp": datetime.now().isoformat(),
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


@router.get("/by-pelanggan/{pelanggan_id}", response_model=List[DataTeknisSchema])
async def read_data_teknis_by_pelanggan(pelanggan_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mengambil data teknis berdasarkan ID pelanggan.
    """
    query = select(DataTeknisModel).options(joinedload(DataTeknisModel.pelanggan)).where(DataTeknisModel.pelanggan_id == pelanggan_id)
    result = await db.execute(query)
    data_teknis_list = list(result.scalars().all())
    return data_teknis_list


@router.get("/", response_model=DataTeknisResponse)
async def read_all_data_teknis(
    skip: int = 0,
    limit: Optional[int] = Query(default=50, le=500, description="Maximum 500 records per request for optimal performance"),
    search: Optional[str] = None,
    olt: Optional[str] = None,
    profile: Optional[str] = None,
    vlan: Optional[str] = None,
    onu_power_min: Optional[int] = None,
    onu_power_max: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua data teknis dengan paginasi, filter, dan total hitungan.
    """
    query = select(DataTeknisModel).options(joinedload(DataTeknisModel.pelanggan))
    count_query = select(func.count(DataTeknisModel.id))

    if search:
        search_term = f"%{search}%"
        # Apply join for searching
        query = query.join(PelangganModel, DataTeknisModel.pelanggan_id == PelangganModel.id).where(
            or_(
                func.coalesce(PelangganModel.nama, "").ilike(search_term),
                func.coalesce(DataTeknisModel.id_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.ip_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.sn, "").ilike(search_term),
            )
        )
        # Apply the same join and where clause to the count query
        count_query = count_query.join(PelangganModel, DataTeknisModel.pelanggan_id == PelangganModel.id).where(
            or_(
                func.coalesce(PelangganModel.nama, "").ilike(search_term),
                func.coalesce(DataTeknisModel.id_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.ip_pelanggan, "").ilike(search_term),
                func.coalesce(DataTeknisModel.sn, "").ilike(search_term),
            )
        )
    else:
        # If no search, still join for eager loading but no where clause for the main query
        query = query.join(DataTeknisModel.pelanggan)
        # Apply join to count_query as well for consistency
        count_query = count_query.join(DataTeknisModel.pelanggan)

    # Filter OLT
    if olt and olt != "Semua":
        query = query.where(DataTeknisModel.olt == olt)
        count_query = count_query.where(DataTeknisModel.olt == olt)

    # Filter Profile PPPoE
    if profile and profile != "Semua":
        query = query.where(DataTeknisModel.profile_pppoe == profile)
        count_query = count_query.where(DataTeknisModel.profile_pppoe == profile)

    # Filter VLAN
    if vlan and vlan != "Semua":
        query = query.where(DataTeknisModel.id_vlan == vlan)
        count_query = count_query.where(DataTeknisModel.id_vlan == vlan)

    # Filter ONU Power Range
    if onu_power_min is not None:
        query = query.where(DataTeknisModel.onu_power >= onu_power_min)
        count_query = count_query.where(DataTeknisModel.onu_power >= onu_power_min)

    if onu_power_max is not None:
        query = query.where(DataTeknisModel.onu_power <= onu_power_max)
        count_query = count_query.where(DataTeknisModel.onu_power <= onu_power_max)

    # Get total count before applying pagination
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar_one()

    # Apply ordering and pagination to the main query
    query = query.order_by(DataTeknisModel.id.desc())
    if limit is not None:
        query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    data_teknis_list = list(result.unique().scalars().all())

    return DataTeknisResponse(data=data_teknis_list, total_count=total_count)  # type: ignore


@router.get("/available-olt", response_model=List[str])
async def get_available_olt(db: AsyncSession = Depends(get_db)):
    """
    Mengambil semua OLT/Mikrotik Server yang tersedia untuk filter dropdown.
    Diubah untuk mengambil dari data_teknis.olt agar sesuai dengan data yang ada.
    """
    try:
        # Ambil semua OLT yang ada di data teknis (sesuai dengan data yang difilter)
        query = select(DataTeknisModel.olt).where(
            DataTeknisModel.olt.isnot(None)
        ).distinct().order_by(DataTeknisModel.olt)
        result = await db.execute(query)
        olt_list = result.scalars().all()

        # Tambahkan opsi "Semua" di awal
        all_options = ["Semua"] + [olt for olt in olt_list if olt]

        return all_options
    except Exception as e:
        logger.error(f"Error mengambil data OLT: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data OLT: {str(e)}"
        )


@router.get("/available-profiles", response_model=List[str])
async def get_all_available_profiles(db: AsyncSession = Depends(get_db)):
    """
    Mengambil semua Profile PPPoE yang tersedia untuk filter dropdown.
    """
    try:
        # Ambil semua profile PPPoE yang unik dari data teknis
        query = select(DataTeknisModel.profile_pppoe).where(
            DataTeknisModel.profile_pppoe.isnot(None)
        ).distinct().order_by(DataTeknisModel.profile_pppoe)
        result = await db.execute(query)
        profiles = result.scalars().all()

        # Tambahkan opsi "Semua" di awal
        all_options = ["Semua"] + [profile for profile in profiles if profile]

        return all_options
    except Exception as e:
        logger.error(f"Error mengambil data profile PPPoE: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data profile PPPoE: {str(e)}"
        )


@router.get("/available-vlans", response_model=List[str])
async def get_available_vlans(db: AsyncSession = Depends(get_db)):
    """
    Mengambil semua VLAN yang tersedia untuk filter dropdown.
    """
    try:
        # Ambil semua VLAN yang unik dari data teknis
        query = select(DataTeknisModel.id_vlan).where(
            DataTeknisModel.id_vlan.isnot(None)
        ).distinct().order_by(DataTeknisModel.id_vlan)
        result = await db.execute(query)
        vlans = result.scalars().all()

        # Tambahkan opsi "Semua" di awal
        all_options = ["Semua"] + [vlan for vlan in vlans if vlan]

        return all_options
    except Exception as e:
        logger.error(f"Error mengambil data VLAN: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data VLAN: {str(e)}"
        )


@router.get("/debug-filter-data")
async def debug_filter_data(db: AsyncSession = Depends(get_db)):
    """
    Endpoint untuk debugging data filter - menampilkan sample data OLT dan VLAN
    """
    try:
        # Ambil sample data untuk debugging
        query = select(
            DataTeknisModel.olt,
            DataTeknisModel.id_vlan,
            func.count(DataTeknisModel.id).label('count')
        ).where(
            DataTeknisModel.olt.isnot(None)
        ).group_by(
            DataTeknisModel.olt,
            DataTeknisModel.id_vlan
        ).order_by(
            DataTeknisModel.olt
        ).limit(20)

        result = await db.execute(query)
        sample_data = result.all()

        return {
            "sample_olt_vlan_combinations": [
                {"olt": row.olt, "vlan": row.id_vlan, "count": row.count}
                for row in sample_data
            ]
        }
    except Exception as e:
        logger.error(f"Error debugging filter data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil data debug: {str(e)}"
        )


@router.get("/onu-power-ranges")
async def get_onu_power_ranges(db: AsyncSession = Depends(get_db)):
    """
    Mengambil range ONU Power untuk filter dropdown.
    """
    try:
        # Ambil data ONU power min dan max
        query = select(
            func.min(DataTeknisModel.onu_power),
            func.max(DataTeknisModel.onu_power)
        ).where(DataTeknisModel.onu_power.isnot(None))
        result = await db.execute(query)
        min_power, max_power = result.one()

        return {
            "min": min_power or 0,
            "max": max_power or 0,
            "ranges": [
                {"label": "Sinyal Baik (>-24 dBm)", "min": -23, "max": 0},
                {"label": "Sinyal Sedang (-27 s/d -24 dBm)", "min": -27, "max": -24},
                {"label": "Sinyal Lemah (<-27 dBm)", "min": -50, "max": -28}
            ]
        }
    except Exception as e:
        logger.error(f"Error mengambil range ONU Power: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengambil range ONU Power: {str(e)}"
        )




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
        options=[joinedload(DataTeknisModel.pelanggan).joinedload(PelangganModel.langganan)],
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

    # Ambil informasi yang dibutuhkan sebelum data dihapus
    id_pelanggan = db_data_teknis.id_pelanggan
    mikrotik_server_id = db_data_teknis.mikrotik_server_id

    # Cari server Mikrotik untuk koneksi
    mikrotik_server = await db.get(MikrotikServerModel, mikrotik_server_id)
    if mikrotik_server:
        # Hubung ke Mikrotik dan hapus PPPoE secret
        try:
            api, connection = mikrotik_service.get_api_connection(mikrotik_server)
            if api:
                mikrotik_service.delete_pppoe_secret(api, id_pelanggan)
        except Exception as e:
            logger.error(f"Gagal menghapus PPPoE secret dari Mikrotik: {e}")
            # Jangan batalkan penghapusan data karena gagal di Mikrotik
        finally:
            if connection:
                # Gunakan connection pooling untuk menutup koneksi
                mikrotik_pool = mikrotik_service.mikrotik_pool
                mikrotik_pool.return_connection(connection, mikrotik_server.host_ip, int(mikrotik_server.port))

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
                    # Gunakan connection pooling untuk menutup koneksi
                    mikrotik_pool = mikrotik_service.mikrotik_pool
                    mikrotik_pool.return_connection(connection, server.host_ip, int(server.port))

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
            "password_pppoe": "change_on_first_login_" + str(uuid.uuid4())[:8],  # Generate secure random password
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
async def export_to_csv_teknis(
    skip: int = 0,
    limit: int = Query(default=1000, le=10000, description="Maximum 10,000 records per export with progress indicator"),  # Production-ready
    search: Optional[str] = None,
    olt: Optional[str] = None,
    profile: Optional[str] = None,
    vlan: Optional[str] = None,
    onu_power_min: Optional[int] = None,
    onu_power_max: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengekspor data teknis ke CSV dengan data relasi yang mudah dibaca dan filter.
    PERFORMANCE OPTIMIZATION: Added pagination to prevent memory issues with large datasets.
    """
    # PERFORMANCE MONITORING: Log export parameters
    print(f"📊 Exporting data teknis CSV: skip={skip}, limit={limit}, search={search}, olt={olt}")

    query = (
        select(DataTeknisModel)
        .options(
            joinedload(DataTeknisModel.pelanggan),
            joinedload(DataTeknisModel.mikrotik_server),
            joinedload(DataTeknisModel.odp),
        )
        .offset(skip)
        .limit(limit)
    )

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

    if olt and olt != "Semua":
        query = query.where(DataTeknisModel.olt == olt)

    if profile and profile != "Semua":
        query = query.where(DataTeknisModel.profile_pppoe == profile)

    if vlan and vlan != "Semua":
        query = query.where(DataTeknisModel.id_vlan == vlan)

    if onu_power_min is not None:
        query = query.where(DataTeknisModel.onu_power >= onu_power_min)

    if onu_power_max is not None:
        query = query.where(DataTeknisModel.onu_power <= onu_power_max)

    query = query.order_by(DataTeknisModel.id.desc())

    result = await db.execute(query)
    data_list = result.scalars().unique().all()

    if not data_list:
        raise HTTPException(status_code=404, detail="Tidak ada data teknis untuk diekspor dengan filter yang diberikan.")

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
                "Nama Mikrotik Server": (d.mikrotik_server.name if d.mikrotik_server else "N/A"),
                "Kode ODP": d.odp.kode_odp if d.odp else "N/A",
                "Port ODP": d.port_odp,
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
            # Gunakan connection pooling untuk menutup koneksi
            mikrotik_pool = mikrotik_service.mikrotik_pool
            mikrotik_pool.return_connection(connection, mikrotik_server_info.host_ip, int(mikrotik_server_info.port))


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
            # Gunakan connection pooling untuk menutup koneksi
            mikrotik_pool = mikrotik_service.mikrotik_pool
            mikrotik_pool.return_connection(connection, server_to_check.host_ip, int(server_to_check.port))


@router.get("/last-ip/{mikrotik_server_id}")
async def get_last_used_ip(mikrotik_server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mendapatkan IP terakhir yang digunakan dari server Mikrotik tertentu.
    """
    # Ambil server Mikrotik untuk validasi dan koneksi
    mikrotik_server = await db.get(MikrotikServerModel, mikrotik_server_id)
    if not mikrotik_server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Server Mikrotik dengan id {mikrotik_server_id} tidak ditemukan."
        )

    # Ambil semua PPP Secrets dari Mikrotik dan ekstrak IP terakhir
    api, connection = mikrotik_service.get_api_connection(mikrotik_server)
    if not api:
        # Jika tidak bisa terhubung ke Mikrotik, kembalikan data dari database
        query = (
            select(DataTeknisModel)
            .where(DataTeknisModel.mikrotik_server_id == mikrotik_server_id)
            .order_by(DataTeknisModel.ip_pelanggan.desc())
            .limit(1)
        )

        result = await db.execute(query)
        last_data_teknis = result.scalar_one_or_none()

        if last_data_teknis and last_data_teknis.ip_pelanggan:
            # Ekstrak angka terakhir dari IP
            ip_parts = last_data_teknis.ip_pelanggan.split(".")
            last_octet = int(ip_parts[-1]) if len(ip_parts) >= 1 else 0

            return {
                "last_ip": last_data_teknis.ip_pelanggan,
                "last_octet": last_octet,
                "message": f"IP terakhir (dari database): {last_data_teknis.ip_pelanggan}",
                "server_name": mikrotik_server.name,
                "source": "database",
            }
        else:
            return {
                "last_ip": None,
                "last_octet": 0,
                "message": f"Belum ada IP yang tercatat di server '{mikrotik_server.name}' (koneksi Mikrotik tidak tersedia)",
                "server_name": mikrotik_server.name,
                "source": "database",
            }

    try:
        # Ambil semua PPP Secrets dari Mikrotik
        try:
            ppp_secrets = mikrotik_service.get_all_ppp_secrets(api)

            if ppp_secrets:
                # Ekstrak IP yang digunakan dari PPP Secrets
                active_ips = []
                for secret in ppp_secrets:
                    if "remote-address" in secret:
                        ip = secret["remote-address"]
                        # Pastikan format IP valid
                        try:
                            # Validasi format IP sederhana
                            ip_parts = ip.split(".")
                            if len(ip_parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in ip_parts):
                                active_ips.append(ip)
                        except:
                            continue  # Lewati jika format IP tidak valid

                if active_ips:
                    # Urutkan IP berdasarkan angka terakhir (oktet ke-4) secara menurun
                    active_ips.sort(key=lambda ip: int(ip.split(".")[-1]), reverse=True)
                    last_ip = active_ips[0]

                    # Ekstrak angka terakhir dari IP
                    ip_parts = last_ip.split(".")
                    last_octet = int(ip_parts[-1]) if len(ip_parts) >= 1 else 0

                    return {
                        "last_ip": last_ip,
                        "last_octet": last_octet,
                        "message": f"IP terakhir di PPP Secrets: {last_ip}",
                        "server_name": mikrotik_server.name,
                        "source": "mikrotik",
                    }
        except Exception as e:
            logger.error(f"Gagal mengambil PPP Secrets dari Mikrotik: {e}")
            # Jika gagal mengambil dari Mikrotik, lanjutkan ke database

        # Jika tidak ada PPP Secrets atau tidak ada IP valid, coba dari database
        query = (
            select(DataTeknisModel)
            .where(DataTeknisModel.mikrotik_server_id == mikrotik_server_id)
            .order_by(DataTeknisModel.ip_pelanggan.desc())
            .limit(1)
        )

        result = await db.execute(query)
        last_data_teknis = result.scalar_one_or_none()

        if last_data_teknis and last_data_teknis.ip_pelanggan:
            # Ekstrak angka terakhir dari IP
            ip_parts = last_data_teknis.ip_pelanggan.split(".")
            last_octet = int(ip_parts[-1]) if len(ip_parts) >= 1 else 0

            return {
                "last_ip": last_data_teknis.ip_pelanggan,
                "last_octet": last_octet,
                "message": f"IP terakhir (dari database): {last_data_teknis.ip_pelanggan}",
                "server_name": mikrotik_server.name,
                "source": "database",
            }
        else:
            return {
                "last_ip": None,
                "last_octet": 0,
                "message": f"Belum ada IP aktif di PPP Secrets atau database server '{mikrotik_server.name}'",
                "server_name": mikrotik_server.name,
                "source": "mikrotik",
            }

    finally:
        if connection:
            # Gunakan connection pooling untuk menutup koneksi
            mikrotik_pool = mikrotik_service.mikrotik_pool
            mikrotik_pool.return_connection(connection, mikrotik_server.host_ip, int(mikrotik_server.port))
