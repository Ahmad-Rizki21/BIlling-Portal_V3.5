# app/models/langganan.py

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import BigInteger, ForeignKey, Date, String, func, Numeric, Column
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan
    from .paket_layanan import PaketLayanan


class Langganan(Base):
    __tablename__ = "langganan"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), index=True)
    paket_layanan_id: Mapped[int] = mapped_column(ForeignKey("paket_layanan.id"))
    status: Mapped[str] = mapped_column(String(100), index=True)
    tgl_jatuh_tempo: Mapped[Date | None] = mapped_column(Date, index=True)
    tgl_invoice_terakhir: Mapped[date | None] = mapped_column(Date, nullable=True)

    # --- PASTIKAN HANYA BARIS YANG BENAR INI YANG ADA ---
    tgl_mulai_langganan = Column(Date, nullable=True)
    tgl_berhenti: Mapped[date | None] = mapped_column(Date, nullable=True)

    metode_pembayaran: Mapped[str] = mapped_column(String(50), default="Otomatis")
    harga_awal: Mapped[float | None] = mapped_column(Numeric(15, 2))

    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="langganan")
    paket_layanan: Mapped["PaketLayanan"] = relationship(back_populates="langganan")
