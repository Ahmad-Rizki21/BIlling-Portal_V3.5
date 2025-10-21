# app/models/permission.py

from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
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
    roles: Mapped[List["Role"]] = relationship(secondary=role_has_permissions, back_populates="permissions", lazy="selectin")
