from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .harga_layanan import HargaLayanan
    from .langganan import Langganan


class PaketLayanan(Base):
    __tablename__ = "paket_layanan"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    id_brand: Mapped[str] = mapped_column(ForeignKey("harga_layanan.id_brand"), nullable=False)
    nama_paket: Mapped[str] = mapped_column(String(191), nullable=False)
    kecepatan: Mapped[int] = mapped_column(nullable=False)
    harga: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    # --- PASTIKAN RELASI INI ADA ---
    harga_layanan: Mapped["HargaLayanan"] = relationship(back_populates="paket_layanan")
    langganan: Mapped[list["Langganan"]] = relationship(back_populates="paket_layanan")
