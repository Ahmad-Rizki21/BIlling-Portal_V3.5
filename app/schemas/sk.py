# app/schemas/sk.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SKBase(BaseModel):
    judul: str
    konten: str
    tipe: str = "Ketentuan"
    versi: Optional[str] = None


class SKCreate(SKBase):
    pass


class SKUpdate(SKBase):
    pass


class SK(SKBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
