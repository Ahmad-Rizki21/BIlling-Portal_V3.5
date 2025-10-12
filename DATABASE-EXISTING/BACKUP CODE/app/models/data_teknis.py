# File: app/models/data_teknis.py

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .mikrotik_server import MikrotikServer
    from .odp import ODP
    from .pelanggan import Pelanggan

class DataTeknis(Base):
    __tablename__ = "data_teknis"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), unique=True, index=True)
    id_vlan: Mapped[str | None] = mapped_column(String(191), nullable=True)
    id_pelanggan: Mapped[str] = mapped_column(String(191), index=True)
    password_pppoe: Mapped[str] = mapped_column(String(191))
    ip_pelanggan: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    profile_pppoe: Mapped[str | None] = mapped_column(String(191), nullable=True)
    olt: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    olt_custom: Mapped[str | None] = mapped_column(String(191), nullable=True)
    pon: Mapped[int | None] = mapped_column(Integer, nullable=True)
    otb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    odc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    # DIHAPUS: Kolom 'odp' integer yang lama, karena akan digantikan oleh odp_id
    # odp: Mapped[int | None] = mapped_column(Integer, nullable=True) 

    onu_power: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sn: Mapped[str | None] = mapped_column(String(191), nullable=True, index=True)
    speedtest_proof: Mapped[str | None] = mapped_column(String(191), nullable=True)

    mikrotik_sync_pending = Column(Boolean, default=False, nullable=False)

    mikrotik_server_id: Mapped[int | None] = mapped_column(ForeignKey("mikrotik_servers.id"))
    mikrotik_server: Mapped["MikrotikServer"] = relationship(back_populates="data_teknis_pelanggan")

    # Kolom foreign key untuk relasi ODP
    odp_id: Mapped[int | None] = mapped_column(ForeignKey("odp.id"))
    
    # ▼▼▼ INI BAGIAN YANG DIPERBAIKI ▼▼▼
    # Relasi ke ODP. Gunakan kutip ganda yang konsisten.
    odp: Mapped["ODP"] = relationship(back_populates="data_teknis")
    
    port_odp: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relasi ke Pelanggan
    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="data_teknis")
    