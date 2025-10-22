# ====================================================================
# MODEL PERMISSION - PERMISSION MANAGEMENT SYSTEM
# ====================================================================
# Model ini mendefinisikan tabel permissions untuk menyimpan data
# permission/ijin akses spesifik yang bisa diberikan kepada role.
#
# Hubungan dengan tabel lain:
# - roles : Role-role yang punya permission ini
# - role_has_permissions : Tabel perantara many-to-many dengan roles
#
# Contoh Permission:
# - create_pelanggan : Bisa tambah data pelanggan baru
# - edit_invoice     : Bisa edit data invoice
# - delete_user      : Bisa hapus user
# - view_reports     : Bisa lihat laporan
# - manage_network   : Bisa manage konfigurasi jaringan
# ====================================================================

from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Impor tabel perantara untuk many-to-many relationship
from .role_has_permissions import role_has_permissions

if TYPE_CHECKING:
    from .role import Role


class Permission(Base):
    """
    Model tabel Permission - nyimpen semua data permission/ijin akses.
    Ini adalah master data untuk sistem permission yang granular.
    """
    __tablename__ = "permissions"

    # ====================================================================
    # FIELD DEFINITIONS - DATA PERMISSION
    # ====================================================================

    # Primary Key - ID unik buat setiap permission
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Data Permission
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)  # Nama permission (contoh: "create_pelanggan")

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Roles - Semua role yang punya permission ini (Many-to-Many)
    # Satu permission bisa dimiliki oleh banyak role
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_has_permissions, back_populates="permissions", lazy="selectin"
    )
