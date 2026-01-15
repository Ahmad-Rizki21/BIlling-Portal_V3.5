# ====================================================================
# MODEL WORK ORDER - HISTORY WO PELANGGAN
# ====================================================================
# Model ini menyimpan history Work Order untuk setiap pelanggan.
# Setiap pelanggan bisa memiliki multiple WO (instalasi baru, upgrade, downgrade, relokasi)
#
# Hubungan dengan tabel lain:
# - pelanggan     : Pelanggan yang memiliki WO ini
# ====================================================================

from __future__ import annotations
from sqlalchemy import BigInteger, String, Date, ForeignKey, Column, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

# Import Base dengan type annotation yang benar buat mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Import models lain buat relationship (dengan TYPE_CHECKING buat circular import prevention)
if TYPE_CHECKING:
    from .pelanggan import Pelanggan


class WorkOrder(Base):
    """
    Model tabel WorkOrder - menyimpan history Work Order untuk setiap pelanggan.
    Setiap pelanggan bisa memiliki multiple WO (instalasi baru, upgrade, downgrade, relokasi).
    """
    __tablename__ = "work_orders"

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign Key ke Pelanggan
    pelanggan_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pelanggan.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Data Work Order
    no_wo: Mapped[str] = mapped_column(String(191), nullable=False, unique=True)  # Format: FTTH - 01 - NEW INSTALLATION
    jenis_wo: Mapped[str] = mapped_column(String(191), nullable=False)  # new installation/relokasi/upgrade/downgrade
    prioritas: Mapped[str] = mapped_column(String(191), nullable=False)  # high/medium/low
    tanggal_wo: Mapped[Date] = mapped_column(Date, nullable=False)  # Tanggal pembuatan WO
    tanggal_target_online: Mapped[Date | None] = mapped_column(Date)  # Target tanggal online

    # Status WO
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN"
    )  # OPEN/postponed/completed/cancelled

    # Notes/Remarks (opsional)
    catatan: Mapped[str | None] = mapped_column(String(500))  # Catatan tambahan

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    pelanggan: Mapped["Pelanggan"] = relationship("Pelanggan", back_populates="work_orders")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
