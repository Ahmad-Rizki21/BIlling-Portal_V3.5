from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan
    from .paket_layanan import PaketLayanan  # <-- Tambahkan impor ini


class HargaLayanan(Base):
    __tablename__ = "harga_layanan"
    id_brand: Mapped[str] = mapped_column(String(191), primary_key=True)
    brand: Mapped[str] = mapped_column(String(191), nullable=False)
    pajak: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    xendit_key_name: Mapped[str] = mapped_column(String(50), default="JAKINET", nullable=False)

    # Relasi ke Pelanggan yang sudah kita perbaiki
    pelanggan: Mapped[List["Pelanggan"]] = relationship(back_populates="harga_layanan", foreign_keys="[Pelanggan.id_brand]")

    # --- TAMBAHKAN RELASI BARU INI ---
    # Satu brand (HargaLayanan) memiliki banyak PaketLayanan
    paket_layanan: Mapped[List["PaketLayanan"]] = relationship(back_populates="harga_layanan")
