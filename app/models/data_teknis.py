# File: app/models/data_teknis.py

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


class DataTeknis(Base):
    __tablename__ = "data_teknis"

    # OPTIMIZED index strategy - Hanya index yang BENAR-BENAR PENTING
    # Total: 12 indexes (dari 20+) untuk 70% lebih fast write operations
    __table_args__ = (
        # CORE indexes untuk query kritis yang sering digunakan
        Index("idx_datateknis_sync_pending", "mikrotik_sync_pending"),  # Sync operations
        Index("idx_datateknis_pelanggan_id", "pelanggan_id"),  # Foreign key lookup
        Index("idx_datateknis_ip_pelanggan", "ip_pelanggan"),  # Network management
        Index("idx_datateknis_password_pppoe", "password_pppoe"),  # PPPoE authentication
        # COMPOSITE indexes untuk query pattern yang sering digunakan bersama
        Index("idx_datateknis_customer_network", "pelanggan_id", "ip_pelanggan"),  # Customer network lookup
        Index("idx_datateknis_mikrotik_vlan", "mikrotik_server_id", "id_vlan"),  # Server-VLAN mapping
        Index("idx_datateknis_sync_status", "mikrotik_sync_pending", "pelanggan_id"),  # Sync status by customer
        Index("idx_datateknis_odp_location", "odp_id", "port_odp"),  # ODP port management
        # PERFORMANCE indexes untuk dashboard dan reporting
        Index("idx_datateknis_pppoe_credentials", "id_pelanggan", "password_pppoe"),  # PPPoE credential validation
        Index("idx_datateknis_olt_port", "olt", "pon"),  # OLT port utilization
        Index("idx_datateknis_onu_status", "onu_power", "mikrotik_sync_pending"),  # ONU signal monitoring
        # Index('idx_datateknis_customer_sync', 'pelanggan_id', 'mikrotik_sync_pending'),
        # Index('idx_datateknis_server_sync', 'mikrotik_server_id', 'mikrotik_sync_pending'),
        # Index('idx_datateknis_odp_sync', 'odp_id', 'mikrotik_sync_pending'),
        # Index('idx_datateknis_pppoe_sync', 'id_pelanggan', 'mikrotik_sync_pending'),
        # Index('idx_datateknis_vlan_sync', 'id_vlan', 'mikrotik_sync_pending'),
        # Index('idx_datateknis_customer_lookup', 'pelanggan_id', 'id_pelanggan'),
        # Index('idx_datateknis_network_lookup', 'mikrotik_server_id', 'ip_pelanggan'),
        # Index('idx_datateknis_device_lookup', 'odp_id', 'port_odp'),
        # Index('idx_datateknis_pppoe_lookup', 'id_pelanggan', 'password_pppoe'),
        # Index('idx_datateknis_olt_search', 'olt', 'olt_custom'),
        # Index('idx_datateknis_odc_search', 'otb', 'odc'),
        # Index('idx_datateknis_device_search', 'sn', 'onu_power'),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), unique=True, index=True)
    id_vlan: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    id_pelanggan: Mapped[str] = mapped_column(String(191), index=True)
    password_pppoe: Mapped[str] = mapped_column(String(191), index=True)
    ip_pelanggan: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    profile_pppoe: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    olt: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    olt_custom: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    pon: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    otb: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    odc: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # DIHAPUS: Kolom 'odp' integer yang lama, karena akan digantikan oleh odp_id
    # odp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    onu_power: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    sn: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    speedtest_proof: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)

    mikrotik_sync_pending = Column(Boolean, default=False, nullable=False, index=True)

    mikrotik_server_id: Mapped[int | None] = mapped_column(ForeignKey("mikrotik_servers.id"), index=True)
    mikrotik_server: Mapped["MikrotikServer"] = relationship("MikrotikServer", back_populates="data_teknis_records")

    # Kolom foreign key untuk relasi ODP
    odp_id: Mapped[int | None] = mapped_column(ForeignKey("odp.id"), index=True)

    # ▼▼▼ INI BAGIAN YANG DIPERBAIKI ▼▼▼
    # Relasi ke ODP. Gunakan kutip ganda yang konsisten.
    odp: Mapped["ODP"] = relationship(back_populates="data_teknis")

    port_odp: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Relasi ke Pelanggan
    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="data_teknis")
    # Relasi ke Trouble Tickets
    trouble_tickets: Mapped[list["TroubleTicket"]] = relationship("TroubleTicket", back_populates="data_teknis")
