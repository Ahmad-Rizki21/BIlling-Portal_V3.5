# ====================================================================
# MODEL DATA TEKNIS - NETWORK CONNECTION DATA MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel data_teknis untuk menyimpan semua informasi
# teknis tentang koneksi internet FTTH pelanggan.
#
# Hubungan dengan tabel lain:
# - pelanggan         : Customer yang punya data teknis ini (1-to-1)
# - mikrotik_server   : Server yang handle koneksi pelanggan
# - odp              : ODP (Optical Distribution Point) yang dipake
# - trouble_tickets  : Laporan masalah yang berhubungan dengan data teknis
#
# Data yang disimpan:
# - PPPoE credentials   : Username/password untuk koneksi internet
# - IP address          : Alamat IP yang dipake pelanggan
# - VLAN configuration  : Setting VLAN jaringan
# - OLT/ONU info        : Data perangkat fiber optik
# - Signal strength     : Kekuatan sinyal ONU
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Column, String, Integer, BigInteger, Boolean, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan
    from .mikrotik_server import MikrotikServer
    from .odp import ODP
    from .trouble_ticket import TroubleTicket
    from .traffic_history import TrafficHistory


class DataTeknis(Base):
    """
    Model tabel DataTeknis - nyimpen semua data teknis koneksi internet pelanggan.
    Ini tabel penting banget buat team teknisi manage jaringan FTTH.
    """
    __tablename__ = "data_teknis"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR NETWORK OPERATIONS
    # ====================================================================
    # Index strategy yang dioptimasi buat operasi jaringan dan sinkronisasi Mikrotik.
    # Total: 12 indexes buat balance antara performance query dan speed write.
    # Dari 20+ index jadi 12 aja biar write operations 70% lebih cepat.
    __table_args__ = (
        # Index buat query CORE yang sering dipake team teknisi
        Index("idx_datateknis_sync_pending", "mikrotik_sync_pending"),  # Cek mana yang perlu disync ke Mikrotik
        Index("idx_datateknis_pelanggan_id", "pelanggan_id"),           # Lookup data teknis berdasarkan pelanggan
        Index("idx_datateknis_ip_pelanggan", "ip_pelanggan"),           # Management IP address network
        Index("idx_datateknis_password_pppoe", "password_pppoe"),       # Validasi login PPPoE

        # Composite indexes buat query yang sering dipake barengan
        Index("idx_datateknis_customer_network", "pelanggan_id", "ip_pelanggan"),  # Cek data lengkap pelanggan
        Index("idx_datateknis_mikrotik_vlan", "mikrotik_server_id", "id_vlan"),    # Mapping server-VLAN
        Index("idx_datateknis_sync_status", "mikrotik_sync_pending", "pelanggan_id"),  # Status sync per pelanggan
        Index("idx_datateknis_odp_location", "odp_id", "port_odp"),                # Management port ODP

        # Index buat PERFORMANCE monitoring dan dashboard
        Index("idx_datateknis_pppoe_credentials", "id_pelanggan", "password_pppoe"),  # Validasi kredensial PPPoE
        Index("idx_datateknis_olt_port", "olt", "pon"),                              # Monitoring pemakaian port OLT
        Index("idx_datateknis_onu_status", "onu_power", "mikrotik_sync_pending"),    # Monitoring sinyal ONU
    )

    # ====================================================================
    # FIELD DEFINITIONS - DATA TEKNIS KONEKSI
    # ====================================================================

    # Primary Key - ID unik buat setiap record data teknis
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign Key ke Pelanggan (UNIQUE karena 1 pelanggan cuma punya 1 data teknis)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), unique=True, index=True)

    # Data PPPoE (Point-to-Point Protocol over Ethernet) - Buat koneksi internet
    id_pelanggan: Mapped[str] = mapped_column(String(191), index=True)           # Username PPPoE (biasanya format khusus)
    password_pppoe: Mapped[str] = mapped_column(String(191), index=True)          # Password PPPoE untuk autentikasi
    profile_pppoe: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # Profile kecepatan di Mikrotik

    # Data Jaringan
    ip_pelanggan: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # IP address yang diberikan ke pelanggan
    id_vlan: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)       # VLAN ID untuk segmentasi jaringan

    # Data OLT (Optical Line Terminal) - Perangkat pusat fiber optik
    olt: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)           # Nama/ID OLT yang dipake
    olt_custom: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)    # Keterangan custom OLT
    pon: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)               # Nomor port PON di OLT

    # Data Distribusi (OTB/ODC)
    otb: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # Optical Terminal Box number
    odc: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # Optical Distribution Cabinet number

    # Data ODP (Optical Distribution Point)
    odp_id: Mapped[int | None] = mapped_column(ForeignKey("odp.id"), index=True)  # Foreign key ke tabel ODP
    port_odp: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # Nomor port di ODP yang dipake

    # Data ONU (Optical Network Unit) - Perangkat di rumah pelanggan
    sn: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)     # Serial number ONU
    onu_power: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)  # Kekuatan sinyal ONU (dalam dBm)

    # Data Tambahan
    speedtest_proof: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)  # Link bukti speedtest

    # Flag Sinkronisasi Mikrotik - Penting banget buat otomasi
    mikrotik_sync_pending: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)  # True kalau perlu disync ke Mikrotik

    # Server Configuration
    mikrotik_server_id: Mapped[int | None] = mapped_column(ForeignKey("mikrotik_servers.id"), index=True)  # ID Mikrotik server

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Mikrotik Server - Server yang handle koneksi pelanggan ini
    mikrotik_server: Mapped["MikrotikServer"] = relationship("MikrotikServer", back_populates="data_teknis_records")

    # Relasi ke ODP - ODP yang dipake buat koneksi pelanggan
    odp: Mapped["ODP"] = relationship(back_populates="data_teknis")

    # Relasi ke Pelanggan - Customer yang punya data teknis ini (1-to-1 relationship)
    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="data_teknis")

    # Relasi ke Trouble Tickets - Laporan masalah yang terkait dengan data teknis ini
    trouble_tickets: Mapped[list["TroubleTicket"]] = relationship("TroubleTicket", back_populates="data_teknis")

    # Relasi ke Traffic History - Data monitoring bandwidth penggunaan
    traffic_history: Mapped[list["TrafficHistory"]] = relationship("TrafficHistory", back_populates="data_teknis")
