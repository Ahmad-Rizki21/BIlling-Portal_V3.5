from typing import Optional

from pydantic import BaseModel, Field


# ====================================================================
# SKEMA DASAR - Mencerminkan semua kolom di model SQLAlchemy
# ====================================================================
class DataTeknisBase(BaseModel):
    pelanggan_id: int
    mikrotik_server_id: Optional[int] = None
    
    # --- Perbaikan Nama Kolom Sesuai Model ---
    odp_id: Optional[int] = None  # Model menggunakan odp_id
    otb: Optional[int] = None     # Model menggunakan otb (tanpa _id)
    odc: Optional[int] = None     # Model menggunakan odc (tanpa _id)
    port_odp: Optional[int] = None # Kolom ini ada di model Anda
    
    id_vlan: Optional[str] = None
    id_pelanggan: Optional[str] = None
    password_pppoe: Optional[str] = None
    ip_pelanggan: Optional[str] = None
    profile_pppoe: Optional[str] = None
    olt: Optional[str] = None
    olt_custom: Optional[str] = None
    pon: Optional[int] = None
    onu_power: Optional[int] = None
    sn: Optional[str] = None
    speedtest_proof: Optional[str] = None

# ====================================================================
# SKEMA CREATE - Untuk payload saat membuat data teknis baru
# ====================================================================
class DataTeknisCreate(DataTeknisBase):
    # Timpa (override) field dari Base untuk membuatnya wajib diisi saat create.
    # Cukup deklarasikan ulang tanpa 'Optional' dan tanpa nilai default.
    
    profile_pppoe: str
    
    # SANGAT DISARANKAN: Jadikan field penting lainnya juga wajib
    id_pelanggan: str
    password_pppoe: str
    ip_pelanggan: str
    mikrotik_server_id: int

# ====================================================================
# SKEMA UPDATE - Untuk payload saat memperbarui data (semua opsional)
# ====================================================================
class DataTeknisUpdate(BaseModel):
    pelanggan_id: Optional[int] = None
    mikrotik_server_id: Optional[int] = None
    
    # --- Perbaikan Nama Kolom Sesuai Model ---
    odp_id: Optional[int] = None
    otb: Optional[int] = None
    odc: Optional[int] = None
    port_odp: Optional[int] = None

    id_vlan: Optional[str] = None
    id_pelanggan: Optional[str] = None
    password_pppoe: Optional[str] = None
    ip_pelanggan: Optional[str] = None
    profile_pppoe: Optional[str] = None
    olt: Optional[str] = None
    olt_custom: Optional[str] = None
    pon: Optional[int] = None
    onu_power: Optional[int] = None
    sn: Optional[str] = None
    speedtest_proof: Optional[str] = None

# ====================================================================
# SKEMA IMPORT - Untuk validasi data dari file CSV
# ====================================================================
class DataTeknisImport(BaseModel):
    email_pelanggan: str
    
    # --- UBAH BAGIAN INI ---
    # Terima 'olt' dari CSV, tapi simpan sebagai 'nama_mikrotik_server' di dalam kode
    nama_mikrotik_server: str = Field(..., alias='olt')
    
    kode_odp: Optional[str] = None
    port_odp: Optional[int] = None
    id_vlan: str
    id_pelanggan: str
    password_pppoe: str
    ip_pelanggan: str
    profile_pppoe: str
    olt_custom: Optional[str] = None
    pon: Optional[int] = None
    otb: Optional[int] = None
    odc: Optional[int] = None
    onu_power: Optional[int] = None
    sn: Optional[str] = None

    class Config:
        from_attributes = True
        # BARU: Aktifkan populasi field berdasarkan alias
        populate_by_name = True 

    class Config:
        from_attributes = True

# ====================================================================
# SKEMA RESPONSE - Data yang dikembalikan oleh API
# ====================================================================
class DataTeknis(DataTeknisBase):
    id: int

    class Config:
        from_attributes = True

class IPCheckRequest(BaseModel):
    ip_address: str
    current_id: Optional[int] = None # Untuk menangani kasus 'Edit'

class IPCheckResponse(BaseModel):
    is_taken: bool
    message: str
    owner_id: Optional[str] = None # Untuk menampilkan ID PPPoE pemilik IP