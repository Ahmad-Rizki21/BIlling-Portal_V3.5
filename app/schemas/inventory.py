from pydantic import BaseModel
from typing import Optional
from datetime import date

class InventoryItemBase(BaseModel):
    serial_number: str
    mac_address: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None
    item_type_id: int
    status_id: int

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemUpdate(BaseModel):
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    location: Optional[str] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None
    item_type_id: Optional[int] = None
    status_id: Optional[int] = None

class InventoryItemType(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class InventoryStatus(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class InventoryItemResponse(InventoryItemBase):
    id: int
    # Kita akan ganti ID dengan nama di response
    item_type: InventoryItemType
    status: InventoryStatus
    class Config: from_attributes = True