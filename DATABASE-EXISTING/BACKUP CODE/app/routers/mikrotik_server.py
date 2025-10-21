from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db

# Impor model dan skema secara langsung
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..schemas.mikrotik_server import MikrotikServer as MikrotikServerSchema
from ..schemas.mikrotik_server import (
    MikrotikServerCreate,
    MikrotikServerUpdate,
)
from ..services import mikrotik_service

# Pastikan variabel 'router' didefinisikan di sini
router = APIRouter(
    prefix="/mikrotik_servers",
    tags=["Mikrotik Servers"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/", response_model=MikrotikServerSchema, status_code=status.HTTP_201_CREATED
)
async def create_mikrotik_server(
    server_data: MikrotikServerCreate, db: AsyncSession = Depends(get_db)
):
    """
    Membuat (mendaftarkan) server Mikrotik baru.
    """
    # Di sini Anda bisa menambahkan enkripsi untuk password sebelum disimpan jika diperlukan
    db_server = MikrotikServerModel(**server_data.model_dump())
    db.add(db_server)
    await db.commit()
    await db.refresh(db_server)
    return db_server


@router.get("/", response_model=List[MikrotikServerSchema])
async def get_all_mikrotik_servers(
    # Tambahkan parameter filter
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    last_connection_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua server Mikrotik yang terdaftar dengan filter.
    """
    query = select(MikrotikServerModel)

    # Filter pencarian umum (Nama Server atau IP)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                MikrotikServerModel.name.ilike(search_term),
                MikrotikServerModel.host_ip.ilike(search_term),
            )
        )

    # Filter berdasarkan status aktif/nonaktif
    if is_active is not None:
        query = query.where(MikrotikServerModel.is_active == is_active)

    # Filter berdasarkan status koneksi terakhir
    if last_connection_status:
        query = query.where(
            MikrotikServerModel.last_connection_status == last_connection_status
        )

    result = await db.execute(query)
    servers = result.scalars().all()
    return servers


@router.get("/{server_id}", response_model=MikrotikServerSchema)
async def get_mikrotik_server_by_id(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Mengambil detail satu server Mikrotik berdasarkan ID.
    """
    db_server = await db.get(MikrotikServerModel, server_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan")
    return db_server


@router.patch("/{server_id}", response_model=MikrotikServerSchema)
async def update_mikrotik_server(
    server_id: int,
    server_update: MikrotikServerUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Memperbarui data server Mikrotik.
    """
    db_server = await db.get(MikrotikServerModel, server_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan")

    update_data = server_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_server, key, value)

    db.add(db_server)
    await db.commit()
    await db.refresh(db_server)
    return db_server


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mikrotik_server(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Menghapus data server Mikrotik dari sistem.
    """
    db_server = await db.get(MikrotikServerModel, server_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan")

    await db.delete(db_server)
    await db.commit()
    return None


# --- ENDPOINT BARU UNTUK TEST KONEKSI ---
@router.post("/{server_id}/test_connection", status_code=status.HTTP_200_OK)
async def test_mikrotik_connection(server_id: int, db: AsyncSession = Depends(get_db)):
    """
    Menguji koneksi ke server Mikrotik berdasarkan data yang tersimpan.
    """
    db_server = await db.get(MikrotikServerModel, server_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Server Mikrotik tidak ditemukan")

    # Panggil fungsi get_api_connection dari layanan Mikrotik
    api, connection = mikrotik_service.get_api_connection(db_server)

    if not connection:
        # Jika koneksi gagal dibuat
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gagal terhubung ke Mikrotik '{db_server.name}'. Periksa IP, username, password, dan port.",
        )

    try:
        # Coba ambil resource sederhana untuk memastikan koneksi benar-benar berfungsi
        routerboard_info = api.get_resource("/system/routerboard").get()
        ros_version = (
            routerboard_info[0].get("current-firmware") if routerboard_info else "N/A"
        )

        # Update status di database jika berhasil
        db_server.last_connection_status = "Success"
        db_server.last_connected_at = datetime.now()
        db_server.ros_version = ros_version
        await db.commit()

        return {
            "status": "success",
            "message": f"Berhasil terhubung ke Mikrotik '{db_server.name}'.",
            "router_os_version": ros_version,
        }
    except Exception as e:
        # Jika ada error lain setelah koneksi berhasil dibuka
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi error setelah terhubung: {str(e)}",
        )
    finally:
        # Selalu pastikan koneksi ditutup
        if connection:
            connection.disconnect()
