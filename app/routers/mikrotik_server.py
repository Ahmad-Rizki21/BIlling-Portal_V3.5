import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.mikrotik_server import MikrotikServer as MikrotikServerModel
from ..schemas.mikrotik_server import MikrotikServer as MikrotikServerSchema
from ..schemas.mikrotik_server import (
    MikrotikServerCreate,
    MikrotikServerUpdate,
)
from ..services import mikrotik_service
from ..services.mikrotik_connection_pool import mikrotik_pool

# Setup logging
logger = logging.getLogger(__name__)

# Pastikan variabel 'router' didefinisikan di sini
router = APIRouter(
    prefix="/mikrotik_servers",
    tags=["Mikrotik Servers"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=MikrotikServerSchema, status_code=status.HTTP_201_CREATED)
async def create_mikrotik_server(server_data: MikrotikServerCreate, db: AsyncSession = Depends(get_db)):
    """
    Membuat (mendaftarkan) server Mikrotik baru.
    """
    server_data_dict = server_data.model_dump()
    db_server = MikrotikServerModel(**server_data_dict)
    db.add(db_server)
    await db.commit()
    await db.refresh(db_server)
    return db_server


@router.get("/", response_model=List[MikrotikServerSchema])
async def get_all_mikrotik_servers(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    last_connection_status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Mengambil daftar semua server Mikrotik yang terdaftar dengan filter.
    """
    query = select(MikrotikServerModel)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                MikrotikServerModel.name.ilike(search_term),
                MikrotikServerModel.host_ip.ilike(search_term),
            )
        )
    if is_active is not None:
        query = query.where(MikrotikServerModel.is_active == is_active)
    if last_connection_status:
        query = query.where(MikrotikServerModel.last_connection_status == last_connection_status)
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
    if "password" in update_data and not update_data["password"]:
        del update_data["password"]

    for key, value in update_data.items():
        setattr(db_server, key, value)

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
    Menguji koneksi ke server Mikrotik tertentu dan menyimpan hasilnya.
    """
    db_server = await db.get(MikrotikServerModel, server_id)
    if not db_server:
        raise HTTPException(status_code=404, detail="Mikrotik Server not found")

    test_result = {}
    http_status_code = status.HTTP_200_OK

    try:
        if not all([db_server.password, db_server.username, db_server.host_ip, db_server.port]):
            raise ValueError("Informasi koneksi tidak lengkap (host, port, user, atau password kosong).")

        device_details = {
            "host": db_server.host_ip,
            "username": db_server.username,
            "password": db_server.password,
            "port": db_server.port,
        }

        loop = asyncio.get_event_loop()
        test_result = await loop.run_in_executor(None, mikrotik_service.perform_routeros_connection, device_details)

    except ValueError as ve:
        test_result = {"status": "failure", "message": str(ve)}
    except Exception as e:
        test_result = {"status": "failure", "message": f"Terjadi error internal: {e}"}

    # Update status di database
    db_server.last_connection_status = test_result.get("status", "failure")
    db_server.last_connection_message = test_result.get("message", "Unknown error")
    db_server.last_connection_time = datetime.now(timezone.utc)

    if test_result.get("status") == "success":
        data = test_result.get("data", {})
        if isinstance(data, dict):
            db_server.ros_version = data.get("ros_version")
        else:
            db_server.ros_version = str(data) if data else None
        http_status_code = status.HTTP_200_OK
    else:
        http_status_code = status.HTTP_400_BAD_REQUEST

    await db.commit()
    await db.refresh(db_server)

    final_response = {"test_result": test_result, "updated_server": db_server}

    return JSONResponse(status_code=http_status_code, content=jsonable_encoder(final_response))


@router.get("/connection-health/{server_id}")
async def get_connection_health(server_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed connection health status for a specific Mikrotik server."""
    try:
        # Get server from database
        result = await db.execute(select(MikrotikServerModel).where(MikrotikServerModel.id == server_id))
        server = result.scalar_one_or_none()

        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Mikrotik server dengan ID {server_id} tidak ditemukan"
            )

        # Get connection health status
        health_status = mikrotik_pool.get_connection_health_status(host_ip=server.host_ip, port=server.port)

        return {"server_id": server_id, "server_name": server.nama_server, "connection_health": health_status}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting connection health for server {server_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengambil status koneksi: {str(e)}"
        )


@router.get("/connection-health")
async def get_all_connection_health():
    """Get connection health status for all Mikrotik servers."""
    try:
        health_status = mikrotik_pool.get_all_servers_health()
        return health_status

    except Exception as e:
        logger.error(f"Error getting all connection health status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengambil status koneksi: {str(e)}"
        )


@router.post("/cleanup-connections")
async def cleanup_connections():
    """Manually trigger cleanup of stale connections."""
    try:
        cleanup_stats = mikrotik_pool.cleanup_stale_connections()
        return {"message": "Connection cleanup completed successfully", "cleanup_statistics": cleanup_stats}

    except Exception as e:
        logger.error(f"Error during connection cleanup: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal membersihkan koneksi: {str(e)}")


@router.get("/pool-config")
async def get_pool_config():
    """Get current connection pool configuration."""
    try:
        config = mikrotik_pool.get_pool_config()
        return {"message": "Pool configuration retrieved successfully", "configuration": config}

    except Exception as e:
        logger.error(f"Error getting pool config: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Gagal mengambil konfigurasi pool: {str(e)}"
        )
