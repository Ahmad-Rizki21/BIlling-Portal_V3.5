from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# Impor tabel perantara
from .role_has_permissions import role_has_permissions

if TYPE_CHECKING:
    from .permission import Permission
    from .user import User


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role", lazy="selectin")

    # TAMBAHKAN/PASTIKAN RELASI INI ADA DAN BENAR
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_has_permissions, back_populates="roles", lazy="selectin"
    )
