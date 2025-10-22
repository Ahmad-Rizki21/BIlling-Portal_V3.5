# ====================================================================
# MODEL ROLE - ROLE MANAGEMENT SYSTEM
# ====================================================================
# Model ini mendefinisikan tabel roles untuk menyimpan data role/hak akses
# yang bisa diberikan kepada pengguna sistem billing FTTH.
#
# Hubungan dengan tabel lain:
# - users        : User-user yang punya role ini
# - permissions  : Permission/ijin yang dimiliki oleh role ini
# - role_has_permissions : Tabel perantara many-to-many dengan permissions
#
# Contoh Role:
# - admin        : Akses penuh ke semua fitur sistem
# - finance      : Akses ke billing, invoice, dan laporan keuangan
# - support      : Akses ke data pelanggan dan trouble ticket
# - teknisi      : Akses ke data teknis dan monitoring jaringan
# ====================================================================

from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import String, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Impor tabel perantara untuk many-to-many relationship
from .role_has_permissions import role_has_permissions

if TYPE_CHECKING:
    from .user import User
    from .permission import Permission


class Role(Base):
    """
    Model tabel Role - nyimpen semua data role/hak akses sistem.
    Ini adalah master data untuk sistem authorization yang kita pake.
    """
    __tablename__ = "roles"

    # ====================================================================
    # FIELD DEFINITIONS - DATA ROLE
    # ====================================================================

    # Primary Key - ID unik buat setiap role
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Data Role
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)  # Nama role (contoh: "admin", "finance")

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Users - Semua user yang punya role ini
    # Satu role bisa dimiliki oleh banyak user
    users: Mapped[List["User"]] = relationship(back_populates="role", lazy="selectin")

    # Relasi ke Permissions - Semua permission yang dimiliki role ini (Many-to-Many)
    # Satu role bisa punya banyak permission, dan satu permission bisa dimiliki banyak role
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_has_permissions, back_populates="roles", lazy="selectin"
    )
