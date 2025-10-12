from typing import Optional

from pydantic import BaseModel


class PaketLayananBase(BaseModel):
    id_brand: str
    nama_paket: str
    kecepatan: int
    harga: float


class PaketLayananCreate(PaketLayananBase):
    pass


class PaketLayananUpdate(BaseModel):
    nama_paket: Optional[str] = None
    kecepatan: Optional[int] = None
    harga: Optional[float] = None


class PaketLayanan(PaketLayananBase):
    id: int

    class Config:
        from_attributes = True
