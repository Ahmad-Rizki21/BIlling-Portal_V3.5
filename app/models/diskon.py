# ====================================================================
# MODEL DISKON - DISCOUNT PER CLUSTER MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel diskon untuk menyimpan data
# diskon yang diterapkan berdasarkan cluster/alamat pelanggan.
#
# Hubungan dengan tabel lain:
# - invoices      : Invoice yang mendapatkan diskon
# - pelanggan     : Pelanggan yang berada di cluster diskon
#
# Contoh diskon:
# - "Diskon Waringin 50%" - Diskon 50% untuk semua pelanggan di cluster Waringin
# - "Promo Tahun Baru" - Diskon 25% untuk cluster tertentu
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import String, Numeric, Boolean, Date, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

# Import Base dengan type annotation yang benar buat mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base


class Diskon(Base):
    """
    Model tabel Diskon - nyimpen data diskon per cluster/alamat.
    Diskon diterapkan otomatis ke invoice pelanggan yang berada di cluster
    yang sesuai saat generate invoice bulanan.
    """
    __tablename__ = "diskon"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR PERFORMANCE
    # ====================================================================
    # Index strategy buat query diskon yang sering dipake
    __table_args__ = (
        Index("idx_diskon_cluster", "cluster"),           # Filter berlaku dalam tampilan diskons
        Index("idx_diskon_active", "is_active"),          # Filter diskon aktif saja
        Index("idx_diskon_tanggal", "tgl_mulai", "tgl_selesai"),  # Filter by periode
    )

    # ====================================================================
    # FIELD DEFINITIONS - DATA DISKON
    # ====================================================================

    # Primary Key - ID unik buat setiap diskon
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Data Diskon
    nama_diskon: Mapped[str] = mapped_column(String(191), nullable=False)  # Nama diskon (contoh: "Diskon Waringin 50%")
    persentase_diskon: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False
    )  # Persentase diskon (0-100)
    cluster: Mapped[str] = mapped_column(
        String(191), nullable=False
    )  # Nama cluster/alamat (contoh: "Waringin")

    # Status & Periode
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )  # Status aktif diskon
    tgl_mulai: Mapped[datetime | None] = mapped_column(
        Date, nullable=True
    )  # Tanggal mulai berlaku (opsional)
    tgl_selesai: Mapped[datetime | None] = mapped_column(
        Date, nullable=True
    )  # Tanggal selesai berlaku (opsional)

    # Timestamps (otomatis diisi oleh database)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )  # Waktu dibuat
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )  # Waktu diupdate

    def to_dict(self):
        """Konversi model ke dictionary format."""
        return {
            "id": self.id,
            "nama_diskon": self.nama_diskon,
            "persentase_diskon": float(self.persentase_diskon) if self.persentase_diskon else 0,
            "cluster": self.cluster,
            "is_active": self.is_active,
            "tgl_mulai": self.tgl_mulai.isoformat() if self.tgl_mulai else None,
            "tgl_selesai": self.tgl_selesai.isoformat() if self.tgl_selesai else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
