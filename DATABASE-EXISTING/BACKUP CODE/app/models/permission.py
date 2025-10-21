# app/models/permission.py

from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# Impor tabel perantara yang sama
from .role_has_permissions import role_has_permissions

if TYPE_CHECKING:
    from .role import Role


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)

    # Definisikan relasi balik ke Role
    roles: Mapped[List["Role"]] = relationship(
        secondary=role_has_permissions, back_populates="permissions"
    )
