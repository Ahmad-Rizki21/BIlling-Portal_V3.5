# app/routers/inventory_status.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database import get_db
from ..models.inventory_status import InventoryStatus as InventoryStatusModel
from ..schemas.inventory_status import (
    InventoryStatus as InventoryStatusSchema,
    InventoryStatusCreate,
    InventoryStatusUpdate,
)

router = APIRouter(prefix="/inventory-statuses", tags=["Inventory Statuses"])


@router.post("/", response_model=InventoryStatusSchema, status_code=status.HTTP_201_CREATED)
async def create_status(status_data: InventoryStatusCreate, db: AsyncSession = Depends(get_db)):
    # Cek duplikat
    res = await db.execute(select(InventoryStatusModel).where(InventoryStatusModel.name == status_data.name))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Status '{status_data.name}' sudah ada.")

    db_status = InventoryStatusModel(**status_data.model_dump())
    db.add(db_status)
    await db.commit()
    await db.refresh(db_status)
    return db_status


@router.get("/", response_model=List[InventoryStatusSchema])
async def get_all_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
    return result.scalars().all()


@router.patch("/{status_id}", response_model=InventoryStatusSchema)
async def update_status(
    status_id: int,
    status_data: InventoryStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    db_status = await db.get(InventoryStatusModel, status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")

    db_status.name = status_data.name
    await db.commit()
    await db.refresh(db_status)
    return db_status


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_status(status_id: int, db: AsyncSession = Depends(get_db)):
    db_status = await db.get(InventoryStatusModel, status_id)
    if not db_status:
        raise HTTPException(status_code=404, detail="Status not found")

    # Tambahkan validasi di sini jika status sedang digunakan oleh item inventaris
    # Untuk saat ini, kita langsung hapus
    await db.delete(db_status)
    await db.commit()
    return
