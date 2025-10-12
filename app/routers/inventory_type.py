# app/routers/inventory_type.py

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database import get_db
from ..models.inventory_item_type import InventoryItemType as InventoryItemTypeModel
from ..schemas.inventory_type import InventoryItemType as InventoryItemTypeSchema
from ..schemas.inventory_type import (
    InventoryItemTypeCreate,
    InventoryItemTypeUpdate,
)

router = APIRouter(prefix="/inventory-types", tags=["Inventory Types"])


@router.post("/", response_model=InventoryItemTypeSchema, status_code=status.HTTP_201_CREATED)
async def create_item_type(
    item_type: InventoryItemTypeCreate,  # Gunakan skema Create
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(InventoryItemTypeModel).where(InventoryItemTypeModel.name == item_type.name))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Tipe item '{item_type.name}' sudah ada.")

    db_item_type = InventoryItemTypeModel(**item_type.model_dump())
    db.add(db_item_type)
    await db.commit()
    await db.refresh(db_item_type)
    return db_item_type


@router.get("/", response_model=List[InventoryItemTypeSchema])
async def get_all_item_types(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
    return res.scalars().all()


@router.patch("/{type_id}", response_model=InventoryItemTypeSchema)
async def update_item_type(type_id: int, item_type: InventoryItemTypeUpdate, db: AsyncSession = Depends(get_db)):
    db_item_type = await db.get(InventoryItemTypeModel, type_id)
    if not db_item_type:
        raise HTTPException(status_code=404, detail="Tipe item tidak ditemukan")

    db_item_type.name = item_type.name
    await db.commit()
    await db.refresh(db_item_type)
    return db_item_type


@router.delete("/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item_type(type_id: int, db: AsyncSession = Depends(get_db)):
    db_item_type = await db.get(InventoryItemTypeModel, type_id)
    if not db_item_type:
        raise HTTPException(status_code=404, detail="Tipe item tidak ditemukan")

    await db.delete(db_item_type)
    await db.commit()
    return
