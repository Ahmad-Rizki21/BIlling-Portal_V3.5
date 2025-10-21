from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .paket_layanan import PaketLayanan  # <-- Tambahkan impor ini
    from .pelanggan import Pelanggan


class HargaLayanan(Base):
    __tablename__ = "harga_layanan"
    id_brand: Mapped[str] = mapped_column(String(191), primary_key=True)
    brand: Mapped[str] = mapped_column(String(191), nullable=False)
    pajak: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    xendit_key_name: Mapped[str] = mapped_column(
        String(50), default="JAKINET", nullable=False
    )

    # Relasi ke Pelanggan yang sudah kita perbaiki
    pelanggan: Mapped[List["Pelanggan"]] = relationship(
        back_populates="harga_layanan", foreign_keys="[Pelanggan.id_brand]"
    )

    # --- TAMBAHKAN RELASI BARU INI ---
    # Satu brand (HargaLayanan) memiliki banyak PaketLayanan
    paket_layanan: Mapped[List["PaketLayanan"]] = relationship(
        back_populates="harga_layanan"
    )
