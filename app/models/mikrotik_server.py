# app/models/mikrotik_server.py

from __future__ import annotations
from typing import List, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, BigInteger, Boolean, func, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base

if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .olt import OLT
    from .pelanggan import Pelanggan


class MikrotikServer(Base):
    __tablename__ = "mikrotik_servers"

    # Optimized index strategy - Hanya index yang BENAR-BENAR PENTING untuk performa
    __table_args__ = (
        # Core composite indexes untuk query dashboard yang sering digunakan
        Index("idx_mikrotik_active_status", "is_active", "last_connection_status"),  # Dashboard filtering
        Index("idx_mikrotik_host_name", "host_ip", "name"),  # Server identification
        Index("idx_mikrotik_active_host", "is_active", "host_ip"),  # Active server lookup
        # Core single indexes untuk lookup cepat
        Index("idx_mikrotik_is_active", "is_active"),  # Filter active servers
        Index("idx_mikrotik_last_connection_status", "last_connection_status"),  # Connection status
        Index("idx_mikrotik_last_connected_at", "last_connected_at"),  # Connection tracking
        Index("idx_mikrotik_ros_version", "ros_version"),  # Version filtering
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False, index=True)  # Unique index untuk server lookup
    host_ip: Mapped[str] = mapped_column(String(191), nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(191), nullable=False, index=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)  # Tidak perlu index untuk password
    port: Mapped[int] = mapped_column(Integer, default=8728, index=True)
    ros_version: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # Sudah ada di composite index
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)  # Sudah ada di composite index
    last_connection_status: Mapped[str | None] = mapped_column(
        String(191), nullable=True, index=True
    )  # Sudah ada di composite index
    last_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True
    )  # Sudah ada di composite index
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now(), index=True)

    # --- TAMBAHKAN RELASI BALIK INI ---
    data_teknis_records: Mapped[List["DataTeknis"]] = relationship("DataTeknis", back_populates="mikrotik_server")
    # -----------------------------------
    olts: Mapped[List["OLT"]] = relationship("OLT", back_populates="mikrotik_server")

    pelanggan: Mapped[list["Pelanggan"]] = relationship("Pelanggan", back_populates="mikrotik_server")
