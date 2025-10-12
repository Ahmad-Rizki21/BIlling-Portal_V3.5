import re
from typing import Optional

from pydantic import BaseModel, Field, validator


# ====================================================================
# SKEMA DASAR - Mencerminkan semua kolom di model SQLAlchemy
# ====================================================================
class DataTeknisBase(BaseModel):
    pelanggan_id: int = Field(..., gt=0, description="ID pelanggan")
    mikrotik_server_id: Optional[int] = Field(None, gt=0, description="ID server Mikrotik")

    # --- Perbaikan Nama Kolom Sesuai Model ---
    odp_id: Optional[int] = Field(None, gt=0, description="ID ODP")
    otb: Optional[int] = Field(None, ge=0, description="ID OTB")
    odc: Optional[int] = Field(None, ge=0, description="ID ODC")
    port_odp: Optional[int] = Field(None, ge=0, le=16, description="Port ODP (1-16)")

    id_vlan: Optional[str] = Field(None, max_length=20, description="ID VLAN")
    id_pelanggan: Optional[str] = Field(None, min_length=1, max_length=100, description="ID pelanggan PPPoE")
    password_pppoe: Optional[str] = Field(None, min_length=1, max_length=100, description="Password PPPoE")
    ip_pelanggan: Optional[str] = Field(None, max_length=15, description="IP pelanggan")
    profile_pppoe: Optional[str] = Field(None, min_length=1, max_length=100, description="Profile PPPoE")
    olt: Optional[str] = Field(None, max_length=100, description="Nama OLT")
    olt_custom: Optional[str] = Field(None, max_length=100, description="Nama OLT kustom")
    pon: Optional[int] = Field(None, ge=0, le=16, description="Port PON (0-16)")
    onu_power: Optional[int] = Field(None, ge=-40, le=10, description="Power ONU (dBm)")
    sn: Optional[str] = Field(None, max_length=50, description="Serial Number perangkat")
    speedtest_proof: Optional[str] = Field(None, max_length=255, description="Bukti speedtest")

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("pelanggan_id", pre=True)
    def validate_pelanggan_id(cls, v):
        if v is None:
            raise ValueError("ID pelanggan tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID pelanggan harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID pelanggan harus lebih besar dari 0")

        return v_int

    @validator("mikrotik_server_id", pre=True)
    def validate_mikrotik_server_id(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID server Mikrotik harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID server Mikrotik harus lebih besar dari 0")

        return v_int

    @validator("odp_id", pre=True)
    def validate_odp_id(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID ODP harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID ODP harus lebih besar dari 0")

        return v_int

    @validator("otb", pre=True)
    def validate_otb(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID OTB harus berupa angka")

        if v_int < 0:
            raise ValueError("ID OTB tidak boleh negatif")

        return v_int

    @validator("odc", pre=True)
    def validate_odc(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID ODC harus berupa angka")

        if v_int < 0:
            raise ValueError("ID ODC tidak boleh negatif")

        return v_int

    @validator("port_odp", pre=True)
    def validate_port_odp(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Port ODP harus berupa angka")

        if v_int < 0 or v_int > 16:
            raise ValueError("Port ODP harus antara 0-16")

        return v_int

    @validator("id_vlan", pre=True)
    def validate_id_vlan(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 20:
            raise ValueError("ID VLAN terlalu panjang (maksimal 20 karakter)")

        return v_str

    @validator("id_pelanggan", pre=True)
    def validate_id_pelanggan(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("ID pelanggan terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9\-_\.]+$", v_str):
            raise ValueError("ID pelanggan hanya boleh mengandung huruf, angka, dash, underscore, dan titik")

        return v_str

    @validator("password_pppoe", pre=True)
    def validate_password_pppoe(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v)
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Password PPPoE terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("ip_pelanggan", pre=True)
    def validate_ip_pelanggan(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 15:
            raise ValueError("IP pelanggan terlalu panjang (maksimal 15 karakter)")

        # Basic IP validation
        ip_parts = v_str.split(".")
        if len(ip_parts) != 4:
            raise ValueError("Format IP tidak valid")

        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError("Format IP tidak valid")
            except ValueError:
                raise ValueError("Format IP tidak valid")

        return v_str

    @validator("profile_pppoe", pre=True)
    def validate_profile_pppoe(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Profile PPPoE terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("olt", pre=True)
    def validate_olt(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Nama OLT terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("olt_custom", pre=True)
    def validate_olt_custom(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Nama OLT kustom terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("pon", pre=True)
    def validate_pon(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Port PON harus berupa angka")

        if v_int < 0 or v_int > 16:
            raise ValueError("Port PON harus antara 0-16")

        return v_int

    @validator("onu_power", pre=True)
    def validate_onu_power(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Power ONU harus berupa angka")

        if v_int < -40 or v_int > 10:
            raise ValueError("Power ONU harus antara -40 dBm sampai 10 dBm")

        return v_int

    @validator("sn", pre=True)
    def validate_sn(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip().upper()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Serial Number terlalu panjang (maksimal 50 karakter)")

        return v_str

    @validator("speedtest_proof", pre=True)
    def validate_speedtest_proof(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 255:
            raise ValueError("Bukti speedtest terlalu panjang (maksimal 255 karakter)")

        return v_str


# ====================================================================
# SKEMA CREATE - Untuk payload saat membuat data teknis baru
# ====================================================================
class DataTeknisCreate(DataTeknisBase):
    # Timpa (override) field dari Base untuk membuatnya wajib diisi saat create.
    # Cukup deklarasikan ulang tanpa 'Optional' dan tanpa nilai default.

    profile_pppoe: str = Field(..., min_length=1, max_length=100, description="Profile PPPoE (wajib)")
    id_pelanggan: str = Field(..., min_length=1, max_length=100, description="ID pelanggan PPPoE (wajib)")
    password_pppoe: str = Field(..., min_length=1, max_length=100, description="Password PPPoE (wajib)")
    ip_pelanggan: str = Field(..., max_length=15, description="IP pelanggan (wajib)")
    mikrotik_server_id: int = Field(..., gt=0, description="ID server Mikrotik (wajib)")

    # Validasi tambahan untuk field wajib
    @validator("profile_pppoe")
    def validate_profile_pppoe_required(cls, v):
        if not v:
            raise ValueError("Profile PPPoE tidak boleh kosong")
        return v

    @validator("id_pelanggan")
    def validate_id_pelanggan_required(cls, v):
        if not v:
            raise ValueError("ID pelanggan tidak boleh kosong")
        return v

    @validator("password_pppoe")
    def validate_password_pppoe_required(cls, v):
        if not v:
            raise ValueError("Password PPPoE tidak boleh kosong")
        return v

    @validator("ip_pelanggan")
    def validate_ip_pelanggan_required(cls, v):
        if not v:
            raise ValueError("IP pelanggan tidak boleh kosong")
        return v

    @validator("mikrotik_server_id")
    def validate_mikrotik_server_id_required(cls, v):
        if not v or v <= 0:
            raise ValueError("ID server Mikrotik tidak boleh kosong dan harus lebih besar dari 0")
        return v

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


# ====================================================================
# SKEMA UPDATE - Untuk payload saat memperbarui data (semua opsional)
# ====================================================================
class DataTeknisUpdate(BaseModel):
    pelanggan_id: Optional[int] = Field(None, gt=0, description="ID pelanggan")
    mikrotik_server_id: Optional[int] = Field(None, gt=0, description="ID server Mikrotik")

    # --- Perbaikan Nama Kolom Sesuai Model ---
    odp_id: Optional[int] = Field(None, gt=0, description="ID ODP")
    otb: Optional[int] = Field(None, ge=0, description="ID OTB")
    odc: Optional[int] = Field(None, ge=0, description="ID ODC")
    port_odp: Optional[int] = Field(None, ge=0, le=16, description="Port ODP (1-16)")

    id_vlan: Optional[str] = Field(None, max_length=20, description="ID VLAN")
    id_pelanggan: Optional[str] = Field(None, min_length=1, max_length=100, description="ID pelanggan PPPoE")
    password_pppoe: Optional[str] = Field(None, min_length=1, max_length=100, description="Password PPPoE")
    ip_pelanggan: Optional[str] = Field(None, max_length=15, description="IP pelanggan")
    profile_pppoe: Optional[str] = Field(None, min_length=1, max_length=100, description="Profile PPPoE")
    olt: Optional[str] = Field(None, max_length=100, description="Nama OLT")
    olt_custom: Optional[str] = Field(None, max_length=100, description="Nama OLT kustom")
    pon: Optional[int] = Field(None, ge=0, le=16, description="Port PON (0-16)")
    onu_power: Optional[int] = Field(None, ge=-40, le=10, description="Power ONU (dBm)")
    sn: Optional[str] = Field(None, max_length=50, description="Serial Number perangkat")
    speedtest_proof: Optional[str] = Field(None, max_length=255, description="Bukti speedtest")

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    # Reuse validator functions (in practice, you might want to create a shared validator module)


# ====================================================================
# SKEMA IMPORT - Untuk validasi data dari file CSV
# ====================================================================
class DataTeknisImport(BaseModel):
    email_pelanggan: str = Field(..., description="Email pelanggan")
    # --- UBAH BAGIAN INI ---
    # Terima 'olt' dari CSV, tapi simpan sebagai 'nama_mikrotik_server' di dalam kode
    nama_mikrotik_server: str = Field(..., alias="olt", description="Nama server Mikrotik")

    kode_odp: Optional[str] = Field(None, max_length=50, description="Kode ODP")
    port_odp: Optional[int] = Field(None, ge=0, le=16, description="Port ODP")
    id_vlan: str = Field(..., max_length=20, description="ID VLAN")
    id_pelanggan: str = Field(..., min_length=1, max_length=100, description="ID pelanggan PPPoE")
    password_pppoe: str = Field(..., min_length=1, max_length=100, description="Password PPPoE")
    ip_pelanggan: str = Field(..., max_length=15, description="IP pelanggan")
    profile_pppoe: str = Field(..., min_length=1, max_length=100, description="Profile PPPoE")
    olt_custom: Optional[str] = Field(None, max_length=100, description="Nama OLT kustom")
    pon: Optional[int] = Field(None, ge=0, le=16, description="Port PON")
    otb: Optional[int] = Field(None, ge=0, description="ID OTB")
    odc: Optional[int] = Field(None, ge=0, description="ID ODC")
    onu_power: Optional[int] = Field(None, ge=-40, le=10, description="Power ONU (dBm)")
    sn: Optional[str] = Field(None, max_length=50, description="Serial Number perangkat")

    class Config:
        from_attributes = True
        # BARU: Aktifkan populasi field berdasarkan alias
        populate_by_name = True
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("email_pelanggan", pre=True)
    def validate_email_pelanggan(cls, v):
        if v is None:
            raise ValueError("Email pelanggan tidak boleh kosong")

        v_str = str(v).strip().lower()
        if not v_str:
            raise ValueError("Email pelanggan tidak boleh kosong")

        # Basic email format check
        if "@" not in v_str or "." not in v_str.split("@")[-1]:
            raise ValueError("Format email tidak valid")

        return v_str

    @validator("nama_mikrotik_server", pre=True)
    def validate_nama_mikrotik_server(cls, v):
        if v is None:
            raise ValueError("Nama server Mikrotik tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama server Mikrotik tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nama server Mikrotik terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("kode_odp", pre=True)
    def validate_kode_odp(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Kode ODP terlalu panjang (maksimal 50 karakter)")

        return v_str

    @validator("port_odp", pre=True)
    def validate_port_odp_import(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Port ODP harus berupa angka")

        if v_int < 0 or v_int > 16:
            raise ValueError("Port ODP harus antara 0-16")

        return v_int

    @validator("id_vlan", pre=True)
    def validate_id_vlan_import(cls, v):
        if v is None:
            raise ValueError("ID VLAN tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("ID VLAN tidak boleh kosong")

        if len(v_str) > 20:
            raise ValueError("ID VLAN terlalu panjang (maksimal 20 karakter)")

        return v_str

    @validator("id_pelanggan", pre=True)
    def validate_id_pelanggan_import(cls, v):
        if v is None:
            raise ValueError("ID pelanggan tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("ID pelanggan tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("ID pelanggan terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9\-_\.]+$", v_str):
            raise ValueError("ID pelanggan hanya boleh mengandung huruf, angka, dash, underscore, dan titik")

        return v_str

    @validator("password_pppoe", pre=True)
    def validate_password_pppoe_import(cls, v):
        if v is None:
            raise ValueError("Password PPPoE tidak boleh kosong")

        v_str = str(v)
        if not v_str:
            raise ValueError("Password PPPoE tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Password PPPoE terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("ip_pelanggan", pre=True)
    def validate_ip_pelanggan_import(cls, v):
        if v is None:
            raise ValueError("IP pelanggan tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("IP pelanggan tidak boleh kosong")

        if len(v_str) > 15:
            raise ValueError("IP pelanggan terlalu panjang (maksimal 15 karakter)")

        # Basic IP validation
        ip_parts = v_str.split(".")
        if len(ip_parts) != 4:
            raise ValueError("Format IP tidak valid")

        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError("Format IP tidak valid")
            except ValueError:
                raise ValueError("Format IP tidak valid")

        return v_str

    @validator("profile_pppoe", pre=True)
    def validate_profile_pppoe_import(cls, v):
        if v is None:
            raise ValueError("Profile PPPoE tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Profile PPPoE tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Profile PPPoE terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("olt_custom", pre=True)
    def validate_olt_custom_import(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Nama OLT kustom terlalu panjang (maksimal 100 karakter)")

        return v_str

    @validator("pon", pre=True)
    def validate_pon_import(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Port PON harus berupa angka")

        if v_int < 0 or v_int > 16:
            raise ValueError("Port PON harus antara 0-16")

        return v_int

    @validator("otb", pre=True)
    def validate_otb_import(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID OTB harus berupa angka")

        if v_int < 0:
            raise ValueError("ID OTB tidak boleh negatif")

        return v_int

    @validator("odc", pre=True)
    def validate_odc_import(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID ODC harus berupa angka")

        if v_int < 0:
            raise ValueError("ID ODC tidak boleh negatif")

        return v_int

    @validator("onu_power", pre=True)
    def validate_onu_power_import(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Power ONU harus berupa angka")

        if v_int < -40 or v_int > 10:
            raise ValueError("Power ONU harus antara -40 dBm sampai 10 dBm")

        return v_int

    @validator("sn", pre=True)
    def validate_sn_import(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip().upper()
        if not v_str:
            return None

        if len(v_str) > 50:
            raise ValueError("Serial Number terlalu panjang (maksimal 50 karakter)")

        return v_str


# ====================================================================
# SKEMA RESPONSE - Data yang dikembalikan oleh API
# ====================================================================
class DataTeknis(DataTeknisBase):
    id: int

    class Config:
        from_attributes = True


class IPCheckRequest(BaseModel):
    ip_address: str = Field(..., max_length=15, description="Alamat IP yang akan dicek")
    current_id: Optional[int] = Field(None, description="ID data teknis saat ini (untuk mode edit)")

    @validator("ip_address", pre=True)
    def validate_ip_address(cls, v):
        if v is None:
            raise ValueError("Alamat IP tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Alamat IP tidak boleh kosong")

        if len(v_str) > 15:
            raise ValueError("Alamat IP terlalu panjang (maksimal 15 karakter)")

        # Basic IP validation
        ip_parts = v_str.split(".")
        if len(ip_parts) != 4:
            raise ValueError("Format IP tidak valid")

        for part in ip_parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    raise ValueError("Format IP tidak valid")
            except ValueError:
                raise ValueError("Format IP tidak valid")

        return v_str

    @validator("current_id", pre=True)
    def validate_current_id(cls, v):
        if v is None or v == "":
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID harus berupa angka")

        if v_int < 0:
            raise ValueError("ID tidak boleh negatif")

        return v_int

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class IPCheckResponse(BaseModel):
    is_taken: bool = Field(..., description="Apakah IP sudah digunakan")
    message: str = Field(..., description="Pesan hasil pengecekan")
    owner_id: Optional[str] = Field(None, description="ID PPPoE pemilik IP (jika ada)")

    @validator("message", pre=True)
    def validate_message(cls, v):
        if v is None:
            return ""

        v_str = str(v)
        if len(v_str) > 200:
            raise ValueError("Pesan terlalu panjang (maksimal 200 karakter)")

        return v_str

    @validator("owner_id", pre=True)
    def validate_owner_id(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("ID pemilik terlalu panjang (maksimal 100 karakter)")

        return v_str

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True
