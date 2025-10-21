# app/models/olt.py

from __future__ import annotations
from typing import List, TYPE_CHECKING

# 1. Tambahkan ForeignKey dan mapped_column
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .odp import ODP
    from .mikrotik_server import MikrotikServer  # <-- Import MikrotikServer


class OLT(Base):
    __tablename__ = "olt"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nama_olt: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    ip_address: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    tipe_olt: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # --- TAMBAHAN UNTUK RELASI KE MIKROTIK ---
    # 2. Tambahkan Foreign Key ke tabel mikrotik_servers
    mikrotik_server_id: Mapped[int | None] = mapped_column(ForeignKey("mikrotik_servers.id"))

    # 3. Tambahkan relasi balik ke model MikrotikServer
    mikrotik_server: Mapped["MikrotikServer"] = relationship(back_populates="olts")
    # --------------------------------------------

    # Relasi ke ODP (ini sudah benar)
    odps: Mapped[List["ODP"]] = relationship(back_populates="olt")
