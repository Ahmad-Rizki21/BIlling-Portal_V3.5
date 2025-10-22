# ====================================================================
# MODEL USER - USER MANAGEMENT & AUTHENTICATION
# ====================================================================
# Model ini mendefinisikan tabel users untuk menyimpan data pengguna
# sistem billing FTTH, termasuk authentication dan authorization.
#
# Hubungan dengan tabel lain:
# - role           : Role/hak akses yang dimiliki user ini
# - activity_logs  : Log aktivitas yang dilakukan user ini
# - token_blacklist : Token yang di-blacklist milik user ini
#
# Jenis User:
# - admin          : Administrator sistem (full access)
# - finance        : Team finance (access billing & invoice)
# - support        : Team customer support (access pelanggan & tiket)
# - teknisi        : Team teknisi (access data teknis & network)
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING, List  # <-- Tambahkan List
from datetime import datetime

from sqlalchemy import String, BigInteger, func, DateTime, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .role import Role
    from .activity_log import ActivityLog  # <-- Tambahkan import ActivityLog
    from .token_blacklist import TokenBlacklist  # <-- Tambahkan import TokenBlacklist


class User(Base):
    """
    Model tabel User - nyimpen semua data user yang bisa login ke sistem.
    Ini adalah tabel autentikasi utama untuk semua pengguna aplikasi.
    """
    __tablename__ = "users"

    # ====================================================================
    # FIELD DEFINITIONS - DATA USER
    # ====================================================================

    # Primary Key - ID unik buat setiap user
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Data Identitas User
    name: Mapped[str] = mapped_column(String(191))                          # Nama lengkap user
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True, nullable=False)  # Email login (unique)

    # Data Autentikasi
    password: Mapped[str] = mapped_column(String(191), nullable=False)      # Password (hash/bcrypt)
    remember_token: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Token buat "remember me"
    email_verified_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)  # Waktu verifikasi email

    # Status User
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)   # User aktif atau tidak

    # Security & Token Management
    revoked_before: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)      # Waktu revokasi token
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Waktu password terakhir diubah

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())  # Waktu user dibuat
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())  # Waktu user diupdate

    # Foreign Key ke Role
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id"))  # ID role yang dimiliki user

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Role - Hak akses yang dimiliki user ini
    # Satu user cuma punya satu role (single role system)
    role: Mapped[Role | None] = relationship(back_populates="users", lazy="selectin")

    # Relasi ke ActivityLog - Semua aktivitas yang dilakukan user ini
    # Satu user bisa punya banyak activity logs
    activity_logs: Mapped[List["ActivityLog"]] = relationship(back_populates="user")

    # Relasi ke TokenBlacklist - Token yang di-blacklist milik user ini
    # Satu user bisa punya banyak blacklisted tokens (security)
    blacklisted_tokens: Mapped[List["TokenBlacklist"]] = relationship(back_populates="user")
