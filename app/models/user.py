from __future__ import annotations
from typing import TYPE_CHECKING, List  # <-- Tambahkan List
from datetime import datetime

from sqlalchemy import String, BigInteger, func, DateTime, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base

from ..database import Base

if TYPE_CHECKING:
    from .role import Role
    from .activity_log import ActivityLog  # <-- Tambahkan import ActivityLog
    from .token_blacklist import TokenBlacklist  # <-- Tambahkan import TokenBlacklist


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(191))
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True, nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    password: Mapped[str] = mapped_column(String(191), nullable=False)
    remember_token: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    revoked_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # AKTIFKAN KEMBALI RELASI INI - Ini adalah kunci perbaikannya
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))
    role: Mapped[Role | None] = relationship(back_populates="users", lazy="selectin")

    # --- TAMBAHKAN RELASI BALIK INI ---
    # Ini memberitahu SQLAlchemy bahwa satu User bisa memiliki banyak ActivityLog
    activity_logs: Mapped[List["ActivityLog"]] = relationship(back_populates="user")

    # --- TAMBAHKAN RELASI UNTUK TOKEN BLACKLIST ---
    # Ini memberitahu SQLAlchemy bahwa satu User bisa memiliki banyak blacklisted tokens
    blacklisted_tokens: Mapped[List["TokenBlacklist"]] = relationship(back_populates="user")
