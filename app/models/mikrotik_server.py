# ====================================================================
# MODEL MIKROTIK SERVER - NETWORK INFRASTRUCTURE MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel mikrotik_servers untuk menyimpan konfigurasi
# dan status semua server Mikrotik yang dipake buat manage jaringan FTTH.
#
# Hubungan dengan tabel lain:
# - data_teknis : Pelanggan-pelanggan yang dihandle oleh server ini
# - olt         : Device OLT yang terhubung ke server ini
# - pelanggan   : Customer yang menggunakan server ini
#
# Fungsi Server:
# - Manajemen PPPoE connections
# - Queue management untuk bandwidth control
# - Firewall rules dan security
# - Monitoring koneksi pelanggan
# ====================================================================

from __future__ import annotations
from typing import List, TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, BigInteger, Boolean, func, DateTime, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .olt import OLT
    from .pelanggan import Pelanggan


class MikrotikServer(Base):
    """
    Model tabel MikrotikServer - nyimpen semua data server Mikrotik.
    Ini adalah master data dari infrastructure jaringan yang kita kelola.
    """
    __tablename__ = "mikrotik_servers"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR NETWORK MONITORING
    # ====================================================================
    # Index strategy yang dioptimasi buat monitoring server dan dashboard network.
    # Fokus pada query yang sering dipake buat cek status koneksi server.
    __table_args__ = (
        # Composite indexes buat query dashboard network team
        Index("idx_mikrotik_active_status", "is_active", "last_connection_status"),  # Filter server aktif & status
        Index("idx_mikrotik_host_name", "host_ip", "name"),                          # Identifikasi server
        Index("idx_mikrotik_active_host", "is_active", "host_ip"),                   # Cari server aktif berdasarkan IP

        # Single indexes buat lookup cepat
        Index("idx_mikrotik_is_active", "is_active"),                     # Filter server yang aktif saja
        Index("idx_mikrotik_last_connection_status", "last_connection_status"),  # Tracking status koneksi
        Index("idx_mikrotik_last_connected_at", "last_connected_at"),     # Monitoring waktu koneksi terakhir
        Index("idx_mikrotik_ros_version", "ros_version"),                 # Filter berdasarkan versi RouterOS
    )

    # ====================================================================
    # FIELD DEFINITIONS - DATA SERVER MIKROTIK
    # ====================================================================

    # Primary Key - ID unik buat setiap server
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Data Identitas Server
    name: Mapped[str] = mapped_column(String(191), unique=True, nullable=False, index=True)  # Nama server (contoh: "MKT-MAIN-01")
    host_ip: Mapped[str] = mapped_column(String(191), nullable=False, index=True)            # IP address server Mikrotik

    # Data Koneksi SSH/API
    username: Mapped[str] = mapped_column(String(191), nullable=False, index=True)           # Username untuk login Mikrotik
    password: Mapped[str] = mapped_column(Text, nullable=False)                              # Password untuk login Mikrotik (encrypted)
    port: Mapped[int] = mapped_column(Integer, default=8728, index=True)                    # Port API Mikrotik (default 8728)

    # Data Status & Monitoring
    ros_version: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # Versi RouterOS (contoh: "7.15")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)               # Server aktif atau tidak
    last_connection_status: Mapped[str | None] = mapped_column(
        String(191), nullable=True, index=True
    )  # Status koneksi terakhir (Connected/Failed/Timeout)
    last_connected_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, index=True
    )  # Waktu koneksi sukses terakhir

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), index=True)  # Waktu server ditambahkan
    updated_at: Mapped[datetime | None] = mapped_column(
        server_default=func.now(), onupdate=func.now(), index=True
    )  # Waktu data server diupdate

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke DataTeknis - Semua pelanggan yang dihandle oleh server ini
    # Satu server bisa handle banyak pelanggan
    data_teknis_records: Mapped[List["DataTeknis"]] = relationship("DataTeknis", back_populates="mikrotik_server")

    # Relasi ke OLT - Device OLT yang terhubung ke server ini
    # Satu server bisa manage beberapa OLT
    olts: Mapped[List["OLT"]] = relationship("OLT", back_populates="mikrotik_server")

    # Relasi ke Pelanggan - Customer yang menggunakan server ini
    # Satu server bisa dipake oleh banyak pelanggan
    pelanggan: Mapped[list["Pelanggan"]] = relationship("Pelanggan", back_populates="mikrotik_server")
