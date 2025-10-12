# app/schemas/inventory_history.py

from datetime import datetime

from pydantic import BaseModel

from .user import UserSimple  # Asumsi Anda punya skema UserSimple (id, nama)


class InventoryHistoryBase(BaseModel):
    id: int
    item_id: int
    action: str
    timestamp: datetime
    user: UserSimple  # Kita akan tampilkan detail user, bukan hanya ID

    class Config:
        from_attributes = True


class InventoryHistoryResponse(InventoryHistoryBase):
    pass
