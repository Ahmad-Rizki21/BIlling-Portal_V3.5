from typing import Optional

from pydantic import BaseModel


class HargaLayananBase(BaseModel):
    id_brand: str
    brand: str
    pajak: float = 11.00
    xendit_key_name: str


class HargaLayananCreate(HargaLayananBase):
    pass


class HargaLayananUpdate(BaseModel):
    brand: Optional[str] = None
    pajak: Optional[float] = None
    xendit_key_name: Optional[str] = None


class HargaLayanan(HargaLayananBase):
    class Config:
        from_attributes = True
