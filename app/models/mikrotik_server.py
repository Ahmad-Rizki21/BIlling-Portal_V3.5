# app/models/mikrotik_server.py

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List  # Pastikan List dan TYPE_CHECKING diimpor

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import (  # Pastikan relationship diimpor
    Mapped,
    mapped_column,
    relationship,
)

from ..database import Base

# Tambahkan blok ini untuk type hinting relasi
if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .olt import OLT
    from .pelanggan import Pelanggan


class MikrotikServer(Base):
    __tablename__ = "mikrotik_servers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False, index=True)
    host_ip: Mapped[str] = mapped_column(String(191), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(191), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=8728)
    ros_version: Mapped[str | None] = mapped_column(String(191), nullable=True)  # Dibuat nullable=True
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    last_connection_status: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # Dibuat nullable=True
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Dibuat nullable=True
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now())

    # --- TAMBAHKAN RELASI BALIK INI ---
    data_teknis_pelanggan: Mapped[List["DataTeknis"]] = relationship(back_populates="mikrotik_server")
    # -----------------------------------
    olts: Mapped[List["OLT"]] = relationship(back_populates="mikrotik_server")

    pelanggan: Mapped[list["Pelanggan"]] = relationship(back_populates="mikrotik_server")
