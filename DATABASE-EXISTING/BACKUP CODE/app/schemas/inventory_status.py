# app/schemas/inventory_status.py

from pydantic import BaseModel


class InventoryStatusBase(BaseModel):
    name: str

class InventoryStatusCreate(InventoryStatusBase):
    pass

# ▼▼▼ KEMUNGKINAN KELAS INI YANG HILANG DARI FILE ANDA ▼▼▼
class InventoryStatusUpdate(InventoryStatusBase):
    pass
# ▲▲▲ PASTIKAN KELAS INI ADA ▲▲▲

class InventoryStatus(InventoryStatusBase):
    id: int

    class Config:
        from_attributes = True