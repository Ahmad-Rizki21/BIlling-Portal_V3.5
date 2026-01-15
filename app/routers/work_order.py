# ====================================================================
# ROUTER WORK ORDER - API ENDPOINTS
# ====================================================================
# Router ini menyediakan endpoints untuk mengelola Work Order (WO).
#
# Endpoints:
# - GET /api/work-orders/next-number: Generate nomor WO berikutnya
# - GET /api/pelanggan/{pelanggan_id}/work-orders: Ambil history WO pelanggan
# - POST /api/pelanggan/{pelanggan_id}/work-orders: Buat WO baru
# - GET /api/work-orders/{wo_id}: Ambil detail WO
# - PUT /api/work-orders/{wo_id}: Update WO
# ====================================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from typing import List
from datetime import date

from ..database import get_db
from ..models.work_order import WorkOrder as WorkOrderModel
from ..models.pelanggan import Pelanggan
from ..models.user import User as UserModel
from ..schemas.work_order import WorkOrderCreate, WorkOrderUpdate, WorkOrder, WorkOrderHistory
from ..auth import get_current_active_user

router = APIRouter(prefix="/work-orders", tags=["Work Orders"])


# ==================== HELPER FUNCTIONS ====================

async def get_next_wo_number(db: AsyncSession) -> str:
    """
    Generate nomor WO berikutnya dengan format: FTTH - XX - JENIS WO
    Contoh: FTTH - 01 - NEW INSTALLATION
    """
    # Cari nomor WO terakhir menggunakan text query untuk menghindari Pydantic attribute error
    from sqlalchemy import text

    result = await db.execute(
        text("SELECT no_wo FROM work_orders ORDER BY created_at DESC LIMIT 1")
    )
    last_wo = result.scalar_one_or_none()

    if last_wo:
        # Extract nomor dari format "FTTH - 01 - NEW INSTALLATION"
        parts = last_wo.split(" - ")
        if len(parts) >= 2:
            try:
                last_number = int(parts[1])
                next_number = last_number + 1
            except ValueError:
                next_number = 1
        else:
            next_number = 1
    else:
        next_number = 1

    # Format nomor dengan 2 digit (01, 02, ..., 99, 100, ...)
    return f"FTTH - {next_number:02d}"


# ==================== API ENDPOINTS ====================

@router.get("/next-number")
async def get_next_wo_number_endpoint(
    jenis_wo: str = "NEW INSTALLATION",
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Generate nomor WO berikutnya
    Query params:
    - jenis_wo: Jenis WO (default: NEW INSTALLATION)
    """
    base_number = await get_next_wo_number(db)
    full_wo_number = f"{base_number} - {jenis_wo.upper()}"
    return {"next_wo_number": full_wo_number}


@router.get("/pelanggan/{pelanggan_id}/work-orders", response_model=List[WorkOrderHistory])
async def get_pelanggan_work_orders(
    pelanggan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Ambil history Work Order untuk pelanggan tertentu
    """
    # Cek apakah pelanggan ada
    result = await db.execute(select(Pelanggan).where(Pelanggan.id == pelanggan_id))
    pelanggan = result.scalar_one_or_none()
    if not pelanggan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pelanggan tidak ditemukan"
        )

    # Ambil semua WO pelanggan (urut dari yang terbaru)
    result = await db.execute(
        select(WorkOrderModel)
        .where(WorkOrderModel.pelanggan_id == pelanggan_id)
        .order_by(desc(WorkOrderModel.created_at))
    )
    work_orders = result.scalars().all()

    # Expunge all objects to prevent lazy loading after session is closed
    for wo in work_orders:
        db.expunge(wo)

    return work_orders


@router.post("/pelanggan/{pelanggan_id}/work-orders", response_model=WorkOrder, status_code=status.HTTP_201_CREATED)
async def create_work_order(
    pelanggan_id: int,
    wo_data: WorkOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Buat Work Order baru untuk pelanggan
    """
    # Cek apakah pelanggan ada
    result = await db.execute(select(Pelanggan).where(Pelanggan.id == pelanggan_id))
    pelanggan = result.scalar_one_or_none()
    if not pelanggan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pelanggan tidak ditemukan"
        )

    # Cek apakah no_wo sudah ada (unique constraint)
    result = await db.execute(
        select(WorkOrderModel).where(WorkOrderModel.no_wo == wo_data.no_wo)
    )
    existing_wo = result.scalar_one_or_none()
    if existing_wo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nomor WO sudah digunakan"
        )

    # Buat WO baru
    new_wo = WorkOrderModel(
        pelanggan_id=pelanggan_id,
        no_wo=wo_data.no_wo,
        jenis_wo=wo_data.jenis_wo,
        prioritas=wo_data.prioritas,
        tanggal_wo=wo_data.tanggal_wo,
        tanggal_target_online=wo_data.tanggal_target_online,
        status=wo_data.status,
        catatan=wo_data.catatan
    )

    db.add(new_wo)
    await db.commit()
    await db.refresh(new_wo)

    # Expunge to prevent lazy loading after session is closed
    db.expunge(new_wo)

    return new_wo


@router.get("/{wo_id}", response_model=WorkOrder)
async def get_work_order(
    wo_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Ambil detail Work Order berdasarkan ID
    """
    result = await db.execute(
        select(WorkOrderModel)
        .where(WorkOrderModel.id == wo_id)
    )
    wo = result.scalar_one_or_none()

    if not wo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work Order tidak ditemukan"
        )

    # Expunge to prevent lazy loading after session is closed
    db.expunge(wo)

    return wo


@router.put("/{wo_id}", response_model=WorkOrder)
async def update_work_order(
    wo_id: int,
    wo_data: WorkOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update Work Order
    """
    result = await db.execute(select(WorkOrderModel).where(WorkOrderModel.id == wo_id))
    wo = result.scalar_one_or_none()

    if not wo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work Order tidak ditemukan"
        )

    # Update field yang diberikan
    update_data = wo_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(wo, field, value)

    await db.commit()
    await db.refresh(wo)

    # Expunge to prevent lazy loading after session is closed
    db.expunge(wo)

    return wo


@router.patch("/{wo_id}/status")
async def update_work_order_status(
    wo_id: int,
    new_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user)
):
    """
    Update status Work Order
    Valid status: OPEN, pending, in_progress, completed, cancelled, COMPLETED
    """
    valid_statuses = ["OPEN", "pending", "in_progress", "completed", "cancelled", "COMPLETED"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status tidak valid. Pilihan: {', '.join(valid_statuses)}"
        )

    result = await db.execute(select(WorkOrderModel).where(WorkOrderModel.id == wo_id))
    wo = result.scalar_one_or_none()

    if not wo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Work Order tidak ditemukan"
        )

    wo.status = new_status
    await db.commit()
    await db.refresh(wo)

    return {"message": "Status berhasil diupdate", "wo_id": wo_id, "new_status": new_status}
