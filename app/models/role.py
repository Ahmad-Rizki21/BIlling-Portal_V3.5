from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import String, BigInteger
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Impor tabel perantara
from .role_has_permissions import role_has_permissions

if TYPE_CHECKING:
    from .user import User
    from .permission import Permission


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False)

    users: Mapped[List["User"]] = relationship(back_populates="role", lazy="selectin")

    # TAMBAHKAN/PASTIKAN RELASI INI ADA DAN BENAR
    permissions: Mapped[List["Permission"]] = relationship(
        secondary=role_has_permissions, back_populates="roles", lazy="selectin"
    )
