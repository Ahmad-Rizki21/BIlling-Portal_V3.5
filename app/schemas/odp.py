# app/schemas/odp.py

from pydantic import BaseModel, Field
from typing import Optional

# Skema OLT sederhana untuk ditampilkan di dalam respons ODP
class OLTSimple(BaseModel):
    id: int
    nama_olt: str

    class Config:
        from_attributes = True

# --- ▼▼▼ TAMBAHAN BARU ▼▼▼ ---
# Skema ODP sederhana untuk menampilkan data parent/induk
# Ini mencegah referensi sirkular (ODP memuat ODP yang memuat ODP, dst.)
class ODPParentSimple(BaseModel):
    id: int
    kode_odp: str

    class Config:
        from_attributes = True
# --- ▲▲▲ AKHIR TAMBAHAN ▲▲▲ ---

class ODPBase(BaseModel):
    kode_odp: str
    alamat: Optional[str] = None
    kapasitas_port: int = 8
    olt_id: int
    
    # --- ▼▼▼ PERUBAHAN DI SINI ▼▼▼ ---
    latitude: Optional[float] = Field(None, description="Garis Lintang lokasi ODP")
    longitude: Optional[float] = Field(None, description="Garis Bujur lokasi ODP")
    parent_odp_id: Optional[int] = Field(None, description="ID dari ODP induk/sebelumnya")
    # --- ▲▲▲ AKHIR PERUBAHAN ▲▲▲ ---


class ODPCreate(ODPBase):
    pass


class ODPUpdate(BaseModel):
    # Dibuat lebih fleksibel, semua field opsional saat update
    kode_odp: Optional[str] = None
    alamat: Optional[str] = None
    kapasitas_port: Optional[int] = None
    olt_id: Optional[int] = None
    
    # --- ▼▼▼ PERUBAHAN DI SINI ▼▼▼ ---
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    parent_odp_id: Optional[int] = None
    # --- ▲▲▲ AKHIR PERUBAHAN ▲▲▲ ---


# Skema respons utama, yang akan dikirim ke frontend
class ODP(ODPBase):
    id: int
    port_terpakai: int = 0
    olt: OLTSimple # Menampilkan detail OLT yang terhubung

    # --- ▼▼▼ TAMBAHAN BARU ▼▼▼ ---
    # Menampilkan detail ODP induk jika ada
    parent_odp: Optional[ODPParentSimple] = None
    # --- ▲▲▲ AKHIR TAMBAHAN ▲▲▲ ---

    class Config:
        from_attributes = True