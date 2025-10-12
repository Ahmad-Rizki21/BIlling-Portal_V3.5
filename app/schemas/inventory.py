import re
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class InventoryItemBase(BaseModel):
    serial_number: str = Field(..., min_length=1, max_length=100, description="Nomor serial perangkat")
    mac_address: Optional[str] = Field(
        None,
        max_length=17,
        description="Alamat MAC perangkat (format: XX:XX:XX:XX:XX:XX)",
    )
    location: Optional[str] = Field(None, max_length=200, description="Lokasi perangkat")
    purchase_date: Optional[date] = Field(None, description="Tanggal pembelian perangkat")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan tambahan")
    item_type_id: int = Field(..., gt=0, description="ID tipe perangkat")
    status_id: int = Field(..., gt=0, description="ID status perangkat")

    @validator("serial_number", pre=True)
    def validate_serial_number(cls, v):
        if v is None:
            raise ValueError("Nomor serial tidak boleh kosong")

        v_str = str(v).strip().upper()
        if not v_str:
            raise ValueError("Nomor serial tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nomor serial terlalu panjang (maksimal 100 karakter)")

        # Remove any non-alphanumeric characters except dashes and underscores
        v_clean = re.sub(r"[^A-Z0-9\-_]", "", v_str)
        if not v_clean:
            raise ValueError("Nomor serial harus mengandung karakter alfanumerik")

        return v_clean

    @validator("mac_address", pre=True)
    def validate_mac_address(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip().upper()
        if not v_str:
            return None

        # Jika input sudah dalam format yang benar (XX:XX:XX:XX:XX:XX), gunakan langsung
        if re.match(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$", v_str):
            return v_str

        # Remove any spaces, colons, dashes, or dots and standardize format
        v_clean = re.sub(r"[^A-F0-9]", "", v_str)

        # Check if it's a valid MAC address (12 hex characters)
        if len(v_clean) != 12:
            # Jika tidak 12 karakter, coba tambahkan padding dengan 0 di depan
            if len(v_clean) < 12:
                v_clean = v_clean.ljust(12, "0")  # Padding dengan 0
            else:
                v_clean = v_clean[:12]  # Potong jika terlalu panjang

        # Validate that all characters are valid hex characters
        v_clean = "".join([c if c in "0123456789ABCDEF" else "0" for c in v_clean])

        # Format as XX:XX:XX:XX:XX:XX
        formatted_mac = ":".join([v_clean[i : i + 2] for i in range(0, 12, 2)])
        return formatted_mac

    @validator("location", pre=True)
    def validate_location(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 200:
            raise ValueError("Lokasi terlalu panjang (maksimal 200 karakter)")

        return v_str

    @validator("notes", pre=True)
    def validate_notes(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 500:
            raise ValueError("Catatan terlalu panjang (maksimal 500 karakter)")

        return v_str

    @validator("item_type_id", pre=True)
    def validate_item_type_id(cls, v):
        if v is None:
            raise ValueError("ID tipe perangkat tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID tipe perangkat harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID tipe perangkat harus lebih besar dari 0")

        return v_int

    @validator("status_id", pre=True)
    def validate_status_id(cls, v):
        if v is None:
            raise ValueError("ID status tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID status harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID status harus lebih besar dari 0")

        return v_int

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class InventoryItemCreate(InventoryItemBase):
    pass

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class InventoryItemUpdate(BaseModel):
    serial_number: Optional[str] = Field(None, min_length=1, max_length=100, description="Nomor serial perangkat")
    mac_address: Optional[str] = Field(
        None,
        max_length=17,
        description="Alamat MAC perangkat (format: XX:XX:XX:XX:XX:XX)",
    )
    location: Optional[str] = Field(None, max_length=200, description="Lokasi perangkat")
    purchase_date: Optional[date] = Field(None, description="Tanggal pembelian perangkat")
    notes: Optional[str] = Field(None, max_length=500, description="Catatan tambahan")
    item_type_id: Optional[int] = Field(None, gt=0, description="ID tipe perangkat")
    status_id: Optional[int] = Field(None, gt=0, description="ID status perangkat")

    @validator("serial_number", pre=True)
    def validate_serial_number_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip().upper()
        if not v_str:
            return None

        if len(v_str) > 100:
            raise ValueError("Nomor serial terlalu panjang (maksimal 100 karakter)")

        # Remove any non-alphanumeric characters except dashes and underscores
        v_clean = re.sub(r"[^A-Z0-9\-_]", "", v_str)
        if not v_clean:
            raise ValueError("Nomor serial harus mengandung karakter alfanumerik")

        return v_clean

    @validator("mac_address", pre=True)
    def validate_mac_address_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip().upper()
        if not v_str:
            return None

        # Remove any spaces or colons and standardize format
        v_clean = re.sub(r"[^A-F0-9]", "", v_str)

        # Check if it's a valid MAC address (12 hex characters)
        if len(v_clean) != 12:
            raise ValueError("Alamat MAC harus terdiri dari 12 karakter hexadesimal (0-9, A-F)")

        # Validate that all characters are valid hex characters
        if not all(c in "0123456789ABCDEF" for c in v_clean):
            raise ValueError("Alamat MAC hanya boleh mengandung karakter hexadesimal (0-9, A-F)")

        # Format as XX:XX:XX:XX:XX:XX
        formatted_mac = ":".join([v_clean[i : i + 2] for i in range(0, 12, 2)])
        return formatted_mac

    @validator("location", pre=True)
    def validate_location_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 200:
            raise ValueError("Lokasi terlalu panjang (maksimal 200 karakter)")

        return v_str

    @validator("notes", pre=True)
    def validate_notes_update(cls, v):
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 500:
            raise ValueError("Catatan terlalu panjang (maksimal 500 karakter)")

        return v_str

    @validator("item_type_id", pre=True)
    def validate_item_type_id_update(cls, v):
        if v is None:
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID tipe perangkat harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID tipe perangkat harus lebih besar dari 0")

        return v_int

    @validator("status_id", pre=True)
    def validate_status_id_update(cls, v):
        if v is None:
            return None

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID status harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID status harus lebih besar dari 0")

        return v_int

    class Config:
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True


class InventoryItemType(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=100, description="Nama tipe perangkat")

    class Config:
        from_attributes = True
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("name", pre=True)
    def validate_name(cls, v):
        if v is None:
            raise ValueError("Nama tipe tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama tipe tidak boleh kosong")

        if len(v_str) > 100:
            raise ValueError("Nama tipe terlalu panjang (maksimal 100 karakter)")

        return v_str


class InventoryStatus(BaseModel):
    id: int
    name: str = Field(..., min_length=1, max_length=50, description="Nama status perangkat")

    class Config:
        from_attributes = True
        # Izinkan field yang tidak didefinisikan dalam model
        extra = "allow"
        # Izinkan assignment nilai
        validate_assignment = True

    @validator("name", pre=True)
    def validate_name(cls, v):
        if v is None:
            raise ValueError("Nama status tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama status tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Nama status terlalu panjang (maksimal 50 karakter)")

        return v_str


class InventoryItemResponse(InventoryItemBase):
    id: int
    # Kita akan ganti ID dengan nama di response
    item_type: InventoryItemType
    status: InventoryStatus


class Config:
    from_attributes = True
    # Izinkan field yang tidak didefinisikan dalam model
    extra = "allow"
    # Izinkan assignment nilai
    validate_assignment = True
