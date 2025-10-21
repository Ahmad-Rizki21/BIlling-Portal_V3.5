from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from .role import Role


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str
    role_id: Optional[int] = None  # Jadikan opsional saat membuat user


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role_id: Optional[int] = None


class User(UserBase):
    id: int
    role_id: Optional[int] = None
    role: Optional[Role] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserSimple(BaseModel):
    id: int
    name: str
    email: EmailStr

    class Config:
        from_attributes = True