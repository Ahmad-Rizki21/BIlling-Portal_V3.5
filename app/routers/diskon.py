# ====================================================================
# ROUTER DISKON - DISCOUNT PER CLUSTER MANAGEMENT API
# ====================================================================
# Router ini menyediakan endpoints untuk mengelola diskon
# berdasarkan cluster/alamat pelanggan.
#
# Fitur:
# - CRUD Diskon (Create, Read, Update, Delete)
# - Filter diskon by cluster
# - Filter diskon aktif/non-aktif
# - Get diskon yang berlaku untuk cluster tertentu
# ====================================================================

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Query,
)
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, distinct
from typing import List, Optional
from datetime import datetime, date
import logging

from ..models.diskon import Diskon as DiskonModel
from ..database import get_db
from ..auth import get_current_active_user
from ..models.user import User as UserModel
from ..models.pelanggan import Pelanggan as PelangganModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/diskon",
    tags=["Diskon"],
    responses={404: {"description": "Not found"}},
)


# ====================================================================
# PYDANTIC SCHEMAS - REQUEST & RESPONSE MODELS
# ====================================================================


class DiskonBase(BaseModel):
    """Base schema untuk diskon"""
    nama_diskon: str = Field(..., min_length=1, max_length=191, description="Nama diskon")
    persentase_diskon: float = Field(..., gt=0, le=100, description="Persentase diskon (0-100)")
    cluster: str = Field(..., min_length=1, max_length=191, description="Nama cluster/alamat")
    is_active: bool = Field(default=True, description="Status aktif diskon")
    tgl_mulai: Optional[date] = Field(None, description="Tanggal mulai berlaku")
    tgl_selesai: Optional[date] = Field(None, description="Tanggal selesai berlaku")


class DiskonCreate(DiskonBase):
    """Schema untuk membuat diskon baru"""
    pass


class DiskonUpdate(BaseModel):
    """Schema untuk update diskon"""
    nama_diskon: Optional[str] = Field(None, min_length=1, max_length=191)
    persentase_diskon: Optional[float] = Field(None, gt=0, le=100)
    cluster: Optional[str] = Field(None, min_length=1, max_length=191)
    is_active: Optional[bool] = None
    tgl_mulai: Optional[date] = None
    tgl_selesai: Optional[date] = None


class DiskonResponse(DiskonBase):
    """Schema untuk response diskon"""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DiskonListResponse(BaseModel):
    """Schema untuk response list diskon"""
    data: List[DiskonResponse]
    total: int
    page: int
    page_size: int


# ====================================================================
# HELPER FUNCTIONS
# ====================================================================


async def check_active_diskon_for_cluster(db: AsyncSession, cluster: str, tanggal: Optional[date] = None) -> Optional[DiskonModel]:
    """
    Cek apakah ada diskon aktif untuk cluster tertentu pada tanggal tertentu.
    Returns diskon dengan persentase terbesar jika ada multiple diskon aktif.
    """
    if tanggal is None:
        tanggal = date.today()

    query = (
        select(DiskonModel)
        .where(DiskonModel.cluster == cluster)
        .where(DiskonModel.is_active == True)
        .where(
            (DiskonModel.tgl_mulai.is_(None)) | (DiskonModel.tgl_mulai <= tanggal)
        )
        .where(
            (DiskonModel.tgl_selesai.is_(None)) | (DiskonModel.tgl_selesai >= tanggal)
        )
        .order_by(DiskonModel.persentase_diskon.desc())
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


# ====================================================================
# API ENDPOINTS - CRUD DISKON
# ====================================================================


@router.get("/", response_model=DiskonListResponse, status_code=status.HTTP_200_OK)
async def get_all_diskon(
    page: int = Query(1, ge=1, description="Nomor halaman"),
    page_size: int = Query(50, ge=1, le=100, description="Jumlah data per halaman"),
    cluster: Optional[str] = Query(None, description="Filter by cluster"),
    is_active: Optional[bool] = Query(None, description="Filter by status aktif"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Mendapatkan semua data diskon dengan pagination dan filter.

    - **page**: Nomor halaman (default: 1)
    - **page_size**: Jumlah data per halaman (default: 50, max: 100)
    - **cluster**: Filter by cluster/alamat (opsional)
    - **is_active**: Filter by status aktif (opsional)
    """
    try:
        # Build query dengan filters
        query = select(DiskonModel)

        if cluster:
            query = query.where(DiskonModel.cluster.ilike(f"%{cluster}%"))
        if is_active is not None:
            query = query.where(DiskonModel.is_active == is_active)

        # Hitung total
        count_query = select(func.count(DiskonModel.id)).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(DiskonModel.created_at.desc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        diskon_list = result.scalars().all()

        return DiskonListResponse(
            data=[DiskonResponse.model_validate(d) for d in diskon_list],
            total=total,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Error getting diskon list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data diskon: {str(e)}"
        )


@router.get("/{diskon_id}", response_model=DiskonResponse, status_code=status.HTTP_200_OK)
async def get_diskon(
    diskon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Mendapatkan detail diskon berdasarkan ID"""
    try:
        query = select(DiskonModel).where(DiskonModel.id == diskon_id)
        result = await db.execute(query)
        diskon = result.scalar_one_or_none()

        if not diskon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diskon dengan ID {diskon_id} tidak ditemukan"
            )

        return DiskonResponse.model_validate(diskon)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diskon {diskon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data diskon: {str(e)}"
        )


@router.get("/cluster/{cluster}", response_model=Optional[DiskonResponse], status_code=status.HTTP_200_OK)
async def get_diskon_by_cluster(
    cluster: str,
    tanggal: Optional[date] = Query(None, description="Tanggal untuk cek diskon (default: hari ini)"),
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Mendapatkan diskon aktif untuk cluster tertentu.
    Returns diskon dengan persentase terbesar jika ada multiple diskon aktif.
    """
    try:
        diskon = await check_active_diskon_for_cluster(db, cluster, tanggal)

        if not diskon:
            return None

        return DiskonResponse.model_validate(diskon)
    except Exception as e:
        logger.error(f"Error getting diskon for cluster {cluster}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan data diskon: {str(e)}"
        )


@router.post("/", response_model=DiskonResponse, status_code=status.HTTP_201_CREATED)
async def create_diskon(
    diskon_data: DiskonCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Membuat diskon baru"""
    try:
        # Validasi tanggal
        if diskon_data.tgl_mulai and diskon_data.tgl_selesai:
            if diskon_data.tgl_mulai > diskon_data.tgl_selesai:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tanggal mulai tidak boleh lebih besar dari tanggal selesai"
                )

        # Buat diskon baru
        new_diskon = DiskonModel(
            nama_diskon=diskon_data.nama_diskon,
            persentase_diskon=diskon_data.persentase_diskon,
            cluster=diskon_data.cluster,
            is_active=diskon_data.is_active,
            tgl_mulai=diskon_data.tgl_mulai,
            tgl_selesai=diskon_data.tgl_selesai,
        )

        db.add(new_diskon)
        await db.commit()
        await db.refresh(new_diskon)

        logger.info(f"Diskon '{diskon_data.nama_diskon}' created by user {current_user.email}")
        return DiskonResponse.model_validate(new_diskon)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating diskon: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal membuat diskon: {str(e)}"
        )


@router.put("/{diskon_id}", response_model=DiskonResponse, status_code=status.HTTP_200_OK)
async def update_diskon(
    diskon_id: int,
    diskon_data: DiskonUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Update data diskon"""
    try:
        # Cari diskon
        query = select(DiskonModel).where(DiskonModel.id == diskon_id)
        result = await db.execute(query)
        diskon = result.scalar_one_or_none()

        if not diskon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diskon dengan ID {diskon_id} tidak ditemukan"
            )

        # Update field yang diberikan
        update_data = diskon_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(diskon, field, value)

        # Validasi tanggal
        if diskon.tgl_mulai and diskon.tgl_selesai:
            if diskon.tgl_mulai > diskon.tgl_selesai:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tanggal mulai tidak boleh lebih besar dari tanggal selesai"
                )

        await db.commit()
        await db.refresh(diskon)

        logger.info(f"Diskon ID {diskon_id} updated by user {current_user.email}")
        return DiskonResponse.model_validate(diskon)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating diskon {diskon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal update diskon: {str(e)}"
        )


@router.delete("/{diskon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_diskon(
    diskon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Hapus diskon dari database"""
    try:
        # Cari diskon
        query = select(DiskonModel).where(DiskonModel.id == diskon_id)
        result = await db.execute(query)
        diskon = result.scalar_one_or_none()

        if not diskon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diskon dengan ID {diskon_id} tidak ditemukan"
            )

        # Hard delete - hapus dari database
        await db.delete(diskon)
        await db.commit()

        logger.info(f"Diskon ID {diskon_id} deleted by user {current_user.email}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error deleting diskon {diskon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal menghapus diskon: {str(e)}"
        )


@router.post("/{diskon_id}/activate", response_model=DiskonResponse, status_code=status.HTTP_200_OK)
async def activate_diskon(
    diskon_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """Aktifkan diskon"""
    try:
        query = select(DiskonModel).where(DiskonModel.id == diskon_id)
        result = await db.execute(query)
        diskon = result.scalar_one_or_none()

        if not diskon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Diskon dengan ID {diskon_id} tidak ditemukan"
            )

        diskon.is_active = True
        await db.commit()
        await db.refresh(diskon)

        logger.info(f"Diskon ID {diskon_id} activated by user {current_user.email}")
        return DiskonResponse.model_validate(diskon)
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error activating diskon {diskon_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mengaktifkan diskon: {str(e)}"
        )


@router.get("/clusters/list", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_cluster_list(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
):
    """
    Mendapatkan daftar cluster/alamat unik dari tabel pelanggan.
    Endpoint ini lebih efisien untuk dropdown cluster tanpa perlu load semua data pelanggan.
    """
    try:
        # Query untuk mendapatkan alamat unik yang tidak null
        query = (
            select(distinct(PelangganModel.alamat))
            .where(PelangganModel.alamat.isnot(None))
            .where(PelangganModel.alamat != "")
            .order_by(PelangganModel.alamat)
        )
        
        result = await db.execute(query)
        clusters = [row[0] for row in result.all() if row[0]]
        
        logger.info(f"Retrieved {len(clusters)} unique clusters")
        return clusters
    except Exception as e:
        logger.error(f"Error getting cluster list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gagal mendapatkan daftar cluster: {str(e)}"
        )
