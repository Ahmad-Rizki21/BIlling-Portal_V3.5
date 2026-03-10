from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime
import logging
import csv
import io
import uuid
from collections import Counter
from pydantic import BaseModel
from fastapi.responses import StreamingResponse

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

from ..auth import get_current_active_user

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
from ..utils.export import create_data_teknis_export_response
from ..services.data_teknis_service import DataTeknisService


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
async def create_data_teknis(
    data_teknis: DataTeknisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Membuat data teknis baru untuk seorang pelanggan."""
    service = DataTeknisService(db)
    return await service.create_data_teknis(data_teknis)


@router.get("/by-pelanggan/{pelanggan_id}", response_model=List[DataTeknisSchema])
async def read_data_teknis_by_pelanggan(
    pelanggan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil data teknis berdasarkan ID pelanggan."""
    service = DataTeknisService(db)
    query = await service.get_filtered_data_teknis_stmt()
    query = query.where(DataTeknisModel.pelanggan_id == pelanggan_id)
    result = await db.execute(query)
    return list(result.unique().scalars().all())


@router.get("/", response_model=DataTeknisResponse)
async def read_all_data_teknis(
    skip: int = 0,
    limit: Optional[int] = Query(default=50, le=500, description="Max 500 records per request"),
    search: Optional[str] = None,
    olt: Optional[str] = None,
    profile: Optional[str] = None,
    vlan: Optional[str] = None,
    onu_power_min: Optional[int] = None,
    onu_power_max: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil daftar semua data teknis dengan paginasi, filter, dan total hitungan."""
    service = DataTeknisService(db)
    query = await service.get_filtered_data_teknis_stmt(
        search=search, olt=olt, profile=profile, vlan=vlan, 
        onu_power_min=onu_power_min, onu_power_max=onu_power_max
    )
    
    # Get total count
    total_count_stmt = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(total_count_stmt)).scalar_one()

    # Apply pagination
    limit = limit or 50
    data_query = query.order_by(DataTeknisModel.id.desc()).offset(skip).limit(limit)
    result = await db.execute(data_query)
    data_list = list(result.unique().scalars().all())

    return DataTeknisResponse(data=data_list, total_count=total_count)


@router.get("/available-olt", response_model=List[str])
async def get_available_olt(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil semua OLT/Mikrotik Server yang tersedia untuk filter dropdown."""
    service = DataTeknisService(db)
    return await service.get_distinct_values("olt")


@router.get("/available-profiles", response_model=List[str])
async def get_available_profiles(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil semua Profile PPPoE yang tersedia untuk filter dropdown."""
    service = DataTeknisService(db)
    return await service.get_distinct_values("profile_pppoe")


@router.get("/available-vlans", response_model=List[str])
async def get_available_vlans(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil semua VLAN yang tersedia untuk filter dropdown."""
    service = DataTeknisService(db)
    return await service.get_distinct_values("id_vlan")


@router.get("/debug-filter-data")
async def debug_filter_data(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
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
async def get_onu_power_ranges(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
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


# GET /data_teknis/export - Export data teknis ke CSV atau Excel
# Buat export data teknis ke file dengan format yang dipilih (CSV/Excel) dengan filter yang sama seperti list
# Query parameters:
# - skip: offset untuk pagination (default: 0)
# - limit: maksimal 10,000 records per export (biar ga crash)
# - search: filter pencarian (sama seperti di list)
# - olt: filter berdasarkan OLT
# - profile: filter berdasarkan profile PPPoE
# - vlan: filter berdasarkan VLAN
# - onu_power_min: filter power ONU minimum
# - onu_power_max: filter power ONU maksimum
# - format: format export (csv atau excel), default csv
# Response: file export dengan semua field data teknis
# Performance optimization: pagination dan eager loading biar ga memory issues
# Format file: CSV dengan BOM atau Excel dengan formatting, timestamp di filename
@router.get("/export", response_class=StreamingResponse)
async def export_data_teknis(
    skip: int = 0,
    limit: int = Query(default=1000, le=10000, description="Maximum 10,000 records per export with progress indicator"),  # Production-ready
    search: Optional[str] = None,
    olt: Optional[str] = None,
    profile: Optional[str] = None,
    vlan: Optional[str] = None,
    onu_power_min: Optional[int] = None,
    onu_power_max: Optional[int] = None,
    format: str = Query("csv", description="Export format: csv atau excel"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Mengekspor data teknis ke CSV atau Excel dengan data relasi yang mudah dibaca dan filter.
    PERFORMANCE OPTIMIZATION: Added pagination to prevent memory issues with large datasets.
    """
    # Validate format
    if format.lower() not in ["csv", "excel", "xlsx"]:
        raise HTTPException(status_code=400, detail="Format tidak valid. Pilih 'csv' atau 'excel'.")

    # PERFORMANCE MONITORING: Log export parameters
    print(f"📊 Exporting data teknis {format}: skip={skip}, limit={limit}, search={search}, olt={olt}")

    service = DataTeknisService(db)
    query = await service.get_filtered_data_teknis_stmt(
        search=search, olt=olt, profile=profile, vlan=vlan,
        onu_power_min=onu_power_min, onu_power_max=onu_power_max
    )
    
    query = query.offset(skip).limit(limit).order_by(DataTeknisModel.id.desc())

    result = await db.execute(query)
    data_list = result.scalars().unique().all()

    if not data_list:
        raise HTTPException(status_code=404, detail="Tidak ada data teknis untuk diekspor dengan filter yang diberikan.")

    # Prepare data untuk export dengan format yang sesuai (lengkap seperti sebelumnya)
    export_data = []
    for d in data_list:
        export_data.append({
            "id_pelanggan": d.id_pelanggan,
            "pelanggan_nama": d.pelanggan.nama if d.pelanggan else "N/A",
            "email_pelanggan": d.pelanggan.email if d.pelanggan else "N/A",
            "alamat": d.pelanggan.alamat if d.pelanggan else "N/A",
            "alamat_2": d.pelanggan.alamat_2 if d.pelanggan else "N/A",
            "no_telp": d.pelanggan.no_telp if d.pelanggan else "N/A",
            "ip_pelanggan": d.ip_pelanggan,
            "profile_pppoe": d.profile_pppoe,
            "vlan": d.id_vlan,
            "sn": d.sn,
            "nama_mikrotik_server": d.mikrotik_server.name if d.mikrotik_server else "N/A",
            "kode_odp": d.odp.kode_odp if d.odp else "N/A",
            "port_odp": d.port_odp,
            "olt_custom": d.olt_custom,
            "pon": d.pon,
            "otb": d.otb,
            "odc": d.odc,
            "onu_power": d.onu_power,
            "status": "Aktif" if d.ip_pelanggan else "Tidak Aktif",
        })

    # Gunakan export utility yang sudah dioptimasi
    return create_data_teknis_export_response(export_data, format.lower())


@router.get("/{data_teknis_id}", response_model=DataTeknisSchema)
async def read_data_teknis_by_id(
    data_teknis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengambil satu data teknis berdasarkan ID."""
    service = DataTeknisService(db)
    return await service.get_by_id_with_relations(
        data_teknis_id, 
        relations=["pelanggan"]
    )


@router.patch("/{data_teknis_id}", response_model=DataTeknisSchema)
async def update_data_teknis(
    data_teknis_id: int,
    data_teknis_update: DataTeknisUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Memperbarui data teknis secara parsial DAN mentrigger update ke Mikrotik."""
    service = DataTeknisService(db)
    return await service.update_data_teknis(data_teknis_id, data_teknis_update)


@router.delete("/{data_teknis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_data_teknis(
    data_teknis_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Menghapus data teknis berdasarkan ID."""
    service = DataTeknisService(db)
    await service.delete_data_teknis(data_teknis_id)
    return None


# Validasi IP
@router.post("/check-ip", response_model=IPCheckResponse)
async def check_ip_address(
    request: IPCheckRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Memeriksa ketersediaan IP address."""
    service = DataTeknisService(db)
    is_taken, message, owner_id = await service.check_ip_availability(request.ip_address, request.current_id)
    return IPCheckResponse(is_taken=is_taken, message=message, owner_id=owner_id)


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

    # Menggunakan semicolon (;) sebagai delimiter agar langsung rapi di Excel (Regional Indonesia/Europe)
    writer = csv.DictWriter(output, fieldnames=headers, delimiter=";")
    writer.writeheader()
    writer.writerows(sample_data)
    output.seek(0)

    response_headers = {"Content-Disposition": 'attachment; filename="template_import_teknis.csv"'}
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        headers=response_headers,
        media_type="text/csv; charset=utf-8",
    )





@router.post("/import/csv")
async def import_from_csv_teknis(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """Mengimpor data teknis dari file CSV dengan validasi relasi."""
    service = DataTeknisService(db)
    return await service.import_from_csv(file)


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
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Menyediakan daftar PPPoE profile yang relevan.
    Logika ini cerdas:
    1. Saat EDIT, ia akan menggunakan server yang sudah tersimpan di data teknis.
    2. Saat CREATE, ia akan menggunakan server yang dipilih di form (dikirim via query param).
    """
    service = DataTeknisService(db)
    return await service.get_available_profiles(paket_layanan_id, pelanggan_id, mikrotik_server_id)


# Perbarui endpoint lama untuk menjaga kompatibilitas, tapi berikan peringatan
@router.get(
    "/available-profiles/{paket_layanan_id}",
    response_model=List[ProfileUsage],
    include_in_schema=False,
)
async def get_available_profiles_legacy(
    paket_layanan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
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

        # MODIFIKASI: Gunakan PPPoE Secrets bukan Active Connections
        # Active connections hanya menampilkan user yang sedang online
        # PPPoE secrets menampilkan SEMUA user yang terdaftar (online maupun offline)
        ppp_secrets = mikrotik_service.get_all_ppp_secrets(api)
        secret_profile_names = [secret.get("profile") for secret in ppp_secrets if "profile" in secret]
        profile_usage_map = Counter(secret_profile_names)

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
async def get_last_used_ip(mikrotik_server_id: int, db: AsyncSession = Depends(get_db), current_user: UserModel = Depends(get_current_active_user)):
    """Mendapatkan IP terakhir yang digunakan dari server Mikrotik tertentu."""
    service = DataTeknisService(db)
    return await service.get_last_used_ip(mikrotik_server_id)
