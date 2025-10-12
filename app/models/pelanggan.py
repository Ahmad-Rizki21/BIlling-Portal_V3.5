from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.data_teknis import DataTeknis

from ..database import Base

if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .harga_layanan import HargaLayanan
    from .invoice import Invoice
    from .langganan import Langganan
    from .mikrotik_server import MikrotikServer


class Pelanggan(Base):
    __tablename__ = "pelanggan"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    no_ktp: Mapped[str] = mapped_column(String(191))
    nama: Mapped[str] = mapped_column(String(191), index=True)
    alamat: Mapped[str] = mapped_column(String(191), index=True)
    alamat_custom: Mapped[str | None] = mapped_column(String(191))
    alamat_2: Mapped[str | None] = mapped_column(Text)
    tgl_instalasi: Mapped[Date | None] = mapped_column(Date)
    blok: Mapped[str] = mapped_column(String(191))
    unit: Mapped[str] = mapped_column(String(191))
    no_telp: Mapped[str] = mapped_column(String(191), index=True)
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True)
    id_brand: Mapped[str | None] = mapped_column(ForeignKey("harga_layanan.id_brand"), index=True)
    layanan: Mapped[str | None] = mapped_column(String(191))
    brand_default: Mapped[str | None] = mapped_column(String(191))

    # --- TAMBAHAN PENTING ---
    mikrotik_server_id: Mapped[Optional[int]] = mapped_column(ForeignKey("mikrotik_servers.id"))
    mikrotik_server: Mapped[Optional["MikrotikServer"]] = relationship(back_populates="pelanggan")
    # --- AKHIR TAMBAHAN ---

    # Relationships
    data_teknis: Mapped["DataTeknis"] = relationship(back_populates="pelanggan", uselist=False, cascade="all, delete-orphan")
    langganan: Mapped[list["Langganan"]] = relationship(back_populates="pelanggan")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="pelanggan")
    harga_layanan: Mapped["HargaLayanan"] = relationship(foreign_keys=[id_brand])

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
