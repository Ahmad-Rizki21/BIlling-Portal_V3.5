import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field, validator

from .role import Role


class UserBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Nama lengkap pengguna (2-100 karakter)",
    )
    email: EmailStr = Field(..., description="Alamat email pengguna")

    @validator("name", pre=True)
    def validate_name(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Nama tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Nama tidak boleh kosong")

        if len(v_str) < 2:
            raise ValueError("Nama harus minimal 2 karakter")

        if len(v_str) > 100:
            raise ValueError("Nama terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters (letters, spaces, dots, dashes, apostrophes)
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v_str):
            raise ValueError("Nama hanya boleh mengandung huruf, spasi, titik, tanda hubung, dan apostrof")

        return v_str.title()  # Capitalize first letter of each word

    @validator("email", pre=True)
    def validate_email_format(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Email tidak boleh kosong")

        v_str = str(v).strip().lower()
        if not v_str:
            raise ValueError("Email tidak boleh kosong")

        # Basic email format check
        if "@" not in v_str or "." not in v_str.split("@")[-1]:
            raise ValueError("Format email tidak valid")

        return v_str


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Kata sandi pengguna (minimal 8 karakter)",
    )
    role_id: Optional[int] = Field(None, description="ID peran pengguna (opsional)")

    @validator("password", pre=True)
    def validate_password(cls, v: Any) -> str:
        if v is None:
            raise ValueError("Kata sandi tidak boleh kosong")

        v_str = str(v)
        if not v_str:
            raise ValueError("Kata sandi tidak boleh kosong")

        if len(v_str) < 8:
            raise ValueError("Kata sandi harus minimal 8 karakter")

        if len(v_str) > 128:
            raise ValueError("Kata sandi terlalu panjang (maksimal 128 karakter)")

        # Check for password complexity
        if not re.search(r"[A-Z]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 huruf kapital")

        if not re.search(r"[a-z]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 huruf kecil")

        if not re.search(r"\d", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 angka")

        # Optional: Check for special characters
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 karakter khusus")

        return v_str


class UserUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nama lengkap pengguna (2-100 karakter)",
    )
    email: Optional[EmailStr] = Field(None, description="Alamat email pengguna")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="Kata sandi pengguna (minimal 8 karakter)",
    )
    role_id: Optional[int] = Field(None, description="ID peran pengguna (opsional)")

    @validator("name", pre=True)
    def validate_name_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return v
        # Reuse the same validation logic as UserBase
        if not isinstance(v, str):
            v = str(v)
        v_str = v.strip()
        if not v_str:
            return None  # Allow clearing the field

        if len(v_str) < 2:
            raise ValueError("Nama harus minimal 2 karakter")

        if len(v_str) > 100:
            raise ValueError("Nama terlalu panjang (maksimal 100 karakter)")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z\s\.\-\']+$", v_str):
            raise ValueError("Nama hanya boleh mengandung huruf, spasi, titik, tanda hubung, dan apostrof")

        return v_str.title()

    @validator("email", pre=True)
    def validate_email_format_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return v

        v_str = str(v).strip().lower()
        if not v_str:
            return None  # Allow clearing the field

        # Basic email format check
        if "@" not in v_str or "." not in v_str.split("@")[-1]:
            raise ValueError("Format email tidak valid")

        return v_str

    @validator("password", pre=True)
    def validate_password_update(cls, v: Any) -> Optional[str]:
        if v is None:
            return v

        v_str = str(v)
        if not v_str:
            return None  # Allow clearing the field

        if len(v_str) < 8:
            raise ValueError("Kata sandi harus minimal 8 karakter")

        if len(v_str) > 128:
            raise ValueError("Kata sandi terlalu panjang (maksimal 128 karakter)")

        # Check for password complexity
        if not re.search(r"[A-Z]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 huruf kapital")

        if not re.search(r"[a-z]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 huruf kecil")

        if not re.search(r"\d", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 angka")

        # Optional: Check for special characters
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v_str):
            raise ValueError("Kata sandi harus mengandung minimal 1 karakter khusus")

        return v_str


class User(UserBase):
    id: int
    role_id: Optional[int] = Field(None, description="ID peran pengguna")
    role: Optional[Role] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserSimple(BaseModel):
    id: int
    name: str = Field(..., description="Nama lengkap pengguna")
    email: EmailStr = Field(..., description="Alamat email pengguna")

    class Config:
        from_attributes = True
