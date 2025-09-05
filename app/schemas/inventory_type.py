# app/schemas/inventory_type.py

from pydantic import BaseModel
from typing import Optional

class InventoryItemTypeBase(BaseModel):
    name: str

class InventoryItemTypeCreate(InventoryItemTypeBase):
    pass

class InventoryItemTypeUpdate(InventoryItemTypeBase):
    pass

class InventoryItemType(InventoryItemTypeBase):
    id: int

    class Config:
        from_attributes = True