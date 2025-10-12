# app/schemas/inventory_type.py

from typing import Optional

from pydantic import BaseModel


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
