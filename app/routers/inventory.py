# app/routers/inventory.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from ..database import get_db
# Import Model dengan alias
from ..models.inventory_item import InventoryItem as InventoryItemModel
from ..models.inventory_item_type import InventoryItemType as InventoryItemTypeModel
from ..models.inventory_status import InventoryStatus as InventoryStatusModel

# Import Skema Pydantic dengan alias
from ..schemas.inventory import (
    InventoryItemCreate, 
    InventoryItemUpdate, 
    InventoryItemResponse,
    InventoryItemType as InventoryItemTypeSchema,
    InventoryStatus as InventoryStatusSchema
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.post("/", response_model=InventoryItemResponse)
async def create_inventory_item(item: InventoryItemCreate, db: AsyncSession = Depends(get_db)):
    db_item = InventoryItemModel(**item.model_dump())
    db.add(db_item)
    await db.commit()
    # Muat relasi secara eksplisit setelah commit
    await db.refresh(db_item, ["item_type", "status"])
    return db_item

@router.get("/", response_model=List[InventoryItemResponse])
async def get_inventory_items(db: AsyncSession = Depends(get_db)):
    query = select(InventoryItemModel).options(
        selectinload(InventoryItemModel.item_type),
        selectinload(InventoryItemModel.status)
    ).order_by(InventoryItemModel.id)
    result = await db.execute(query)
    return result.scalars().all()

@router.patch("/{item_id}", response_model=InventoryItemResponse)
async def update_inventory_item(item_id: int, item_update: InventoryItemUpdate, db: AsyncSession = Depends(get_db)):
    db_item = await db.get(InventoryItemModel, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = item_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
        
    await db.commit()
    await db.refresh(db_item, ["item_type", "status"])
    return db_item

@router.delete("/{item_id}", status_code=204)
async def delete_inventory_item(item_id: int, db: AsyncSession = Depends(get_db)):
    db_item = await db.get(InventoryItemModel, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(db_item)
    await db.commit()
    return

# Helper endpoints untuk dropdown
@router.get("/types", response_model=List[InventoryItemTypeSchema])
async def get_item_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryItemTypeModel).order_by(InventoryItemTypeModel.name))
    return result.scalars().all()

@router.get("/statuses", response_model=List[InventoryStatusSchema])
async def get_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryStatusModel).order_by(InventoryStatusModel.name))
    return result.scalars().all()