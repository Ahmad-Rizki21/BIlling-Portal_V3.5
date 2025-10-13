# app/schemas/token_blacklist.py

import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class TokenBlacklistBase(BaseModel):
    """Base schema for token blacklist"""

    jti: str = Field(..., min_length=1, max_length=36, description="JWT ID (UUID)")
    user_id: int = Field(..., gt=0, description="User ID")
    token_type: str = Field(..., min_length=1, max_length=50, description="Token type (access/refresh)")
    expires_at: datetime = Field(..., description="Token expiration time")
    revoked: bool = Field(False, description="Whether token is revoked")
    revoked_at: Optional[datetime] = Field(None, description="Revocation time")
    revoked_reason: Optional[str] = Field(None, max_length=255, description="Reason for revocation")

    @validator("jti", pre=True)
    def validate_jti(cls, v: Any) -> str:
        """Validate JWT ID format"""
        if v is None:
            raise ValueError("JWT ID tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("JWT ID tidak boleh kosong")

        if len(v_str) > 36:
            raise ValueError("JWT ID terlalu panjang (maksimal 36 karakter)")

        # Basic UUID format validation
        if not re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", v_str, re.IGNORECASE):
            # Allow simpler formats too
            if not re.match(r"^[a-zA-Z0-9\-_]+$", v_str):
                raise ValueError("Format JWT ID tidak valid")

        return v_str

    @validator("user_id", pre=True)
    def validate_user_id(cls, v: Any) -> int:
        """Validate user ID"""
        if v is None:
            raise ValueError("User ID tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("User ID harus berupa angka")

        if v_int <= 0:
            raise ValueError("User ID harus lebih besar dari 0")

        return v_int

    @validator("token_type", pre=True)
    def validate_token_type(cls, v: Any) -> str:
        """Validate token type"""
        if v is None:
            raise ValueError("Tipe token tidak boleh kosong")

        v_str = str(v).strip().lower()
        if not v_str:
            raise ValueError("Tipe token tidak boleh kosong")

        if len(v_str) > 50:
            raise ValueError("Tipe token terlalu panjang (maksimal 50 karakter)")

        valid_types = ["access", "refresh"]
        if v_str not in valid_types:
            raise ValueError(f"Tipe token tidak valid. Pilihan yang tersedia: {', '.join(valid_types)}")

        return v_str.title()  # Capitalize first letter

    @validator("expires_at", pre=True)
    def validate_expires_at(cls, v: Any) -> datetime:
        """Validate expiration time"""
        if v is None:
            raise ValueError("Waktu kedaluwarsa tidak boleh kosong")

        if isinstance(v, str):
            try:
                # Try to parse string datetime
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Format waktu kedaluwarsa tidak valid")

        if not isinstance(v, datetime):
            raise ValueError("Waktu kedaluwarsa harus berupa datetime")

        return v

    @validator("revoked_reason", pre=True)
    def validate_revoked_reason(cls, v: Any) -> Optional[str]:
        """Validate revocation reason"""
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 255:
            raise ValueError("Alasan pencabutan terlalu panjang (maksimal 255 karakter)")

        return v_str


class TokenBlacklistCreate(TokenBlacklistBase):
    """Schema for creating token blacklist entry"""

    revoked: bool = Field(False, description="Whether token is revoked")
    revoked_at: Optional[datetime] = Field(None, description="Revocation time")
    revoked_reason: Optional[str] = Field(None, max_length=255, description="Reason for revocation")


class TokenBlacklistUpdate(BaseModel):
    """Schema for updating token blacklist entry"""

    revoked: Optional[bool] = Field(None, description="Whether token is revoked")
    revoked_at: Optional[datetime] = Field(None, description="Revocation time")
    revoked_reason: Optional[str] = Field(None, max_length=255, description="Reason for revocation")

    @validator("revoked_reason", pre=True)
    def validate_revoked_reason_update(cls, v: Any) -> Optional[str]:
        """Validate revocation reason for update"""
        if v is None or v == "":
            return None

        v_str = str(v).strip()
        if not v_str:
            return None

        if len(v_str) > 255:
            raise ValueError("Alasan pencabutan terlalu panjang (maksimal 255 karakter)")

        return v_str


class TokenBlacklist(TokenBlacklistBase):
    """Schema for token blacklist response"""

    id: int = Field(..., gt=0, description="Token blacklist ID")
    created_at: datetime = Field(..., description="Creation time")

    @validator("id", pre=True)
    def validate_id(cls, v: Any) -> int:
        """Validate ID"""
        if v is None:
            raise ValueError("ID tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("ID harus berupa angka")

        if v_int <= 0:
            raise ValueError("ID harus lebih besar dari 0")

        return v_int

    @validator("created_at", pre=True)
    def validate_created_at(cls, v: Any) -> datetime:
        """Validate creation time"""
        if v is None:
            raise ValueError("Waktu pembuatan tidak boleh kosong")

        if isinstance(v, str):
            try:
                # Try to parse string datetime
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError:
                raise ValueError("Format waktu pembuatan tidak valid")

        if not isinstance(v, datetime):
            raise ValueError("Waktu pembuatan harus berupa datetime")

        return v

    class Config:
        from_attributes = True


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""

    refresh_token: str = Field(..., min_length=1, description="Refresh token")

    @validator("refresh_token", pre=True)
    def validate_refresh_token(cls, v: Any) -> str:
        """Validate refresh token"""
        if v is None:
            raise ValueError("Refresh token tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Refresh token tidak boleh kosong")

        if len(v_str) < 10:
            raise ValueError("Refresh token terlalu pendek")

        if len(v_str) > 500:
            raise ValueError("Refresh token terlalu panjang")

        return v_str


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""

    access_token: str = Field(..., min_length=1, description="New access token")
    refresh_token: str = Field(..., min_length=1, description="New refresh token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., gt=0, description="Access token expiration time in seconds")

    @validator("access_token", pre=True)
    def validate_access_token(cls, v: Any) -> str:
        """Validate access token"""
        if v is None:
            raise ValueError("Access token tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Access token tidak boleh kosong")

        if len(v_str) < 10:
            raise ValueError("Access token terlalu pendek")

        if len(v_str) > 1000:
            raise ValueError("Access token terlalu panjang")

        return v_str

    @validator("refresh_token", pre=True)
    def validate_refresh_token_response(cls, v: Any) -> str:
        """Validate refresh token in response"""
        if v is None:
            raise ValueError("Refresh token tidak boleh kosong")

        v_str = str(v).strip()
        if not v_str:
            raise ValueError("Refresh token tidak boleh kosong")

        if len(v_str) < 10:
            raise ValueError("Refresh token terlalu pendek")

        if len(v_str) > 500:
            raise ValueError("Refresh token terlalu panjang")

        return v_str

    @validator("token_type", pre=True)
    def validate_token_type_response(cls, v: Any) -> str:
        """Validate token type in response"""
        if v is None:
            v = "bearer"

        v_str = str(v).strip().lower()
        if not v_str:
            v_str = "bearer"

        if len(v_str) > 20:
            raise ValueError("Tipe token terlalu panjang")

        if v_str not in ["bearer", "bearer"]:
            raise ValueError("Tipe token tidak valid")

        return v_str

    @validator("expires_in", pre=True)
    def validate_expires_in(cls, v: Any) -> int:
        """Validate expiration time in seconds"""
        if v is None:
            raise ValueError("Waktu kedaluwarsa tidak boleh kosong")

        try:
            v_int = int(v)
        except (ValueError, TypeError):
            raise ValueError("Waktu kedaluwarsa harus berupa angka")

        if v_int <= 0:
            raise ValueError("Waktu kedaluwarsa harus lebih besar dari 0")

        return v_int

    class Config:
        from_attributes = True
