# app/schemas/olt.py
from pydantic import BaseModel
from typing import Optional

class OLTBase(BaseModel):
    nama_olt: str
    ip_address: str
    tipe_olt: str
    username: Optional[str] = None
    # TAMBAHKAN INI: ID Mikrotik yang akan dihubungkan, wajib saat membuat
    mikrotik_server_id: int

class OLTCreate(OLTBase):
    password: Optional[str] = None

class OLTUpdate(BaseModel):
    nama_olt: Optional[str] = None
    ip_address: Optional[str] = None
    tipe_olt: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    # TAMBAHKAN INI: Agar bisa mengubah koneksi Mikrotik saat edit
    mikrotik_server_id: Optional[int] = None

class OLT(OLTBase):
    id: int

    class Config:
        from_attributes = True
