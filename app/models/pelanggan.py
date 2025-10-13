# app/models/pelanggan.py

from __future__ import annotations
from sqlalchemy import BigInteger, String, Date, Text, ForeignKey, Column, Integer, Index, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING, Optional
from datetime import datetime

from ..database import Base

if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .langganan import Langganan
    from .invoice import Invoice
    from .harga_layanan import HargaLayanan
    from .mikrotik_server import MikrotikServer
    from .inventory_item import InventoryItem


class Pelanggan(Base):
    __tablename__ = "pelanggan"

    # OPTIMIZED index strategy - Hanya index yang BENAR-BENAR PENTING untuk performa
    # Total: 8 indexes (dari 9+) untuk maximum performance dengan minimum overhead
    __table_args__ = (
        # CORE indexes untuk query yang sering digunakan
        Index("idx_pelanggan_nama_alamat", "nama", "alamat"),  # Search pelanggan
        Index("idx_pelanggan_blok_unit", "blok", "unit"),  # Pencarian lokasi
        Index("idx_pelanggan_brand_status", "id_brand", "layanan"),  # Filter brand & layanan
        Index("idx_pelanggan_ktp_email", "no_ktp", "email"),  # Validasi unik KTP & email
        # PERFORMANCE indexes untuk dashboard dan reporting
        Index("idx_pelanggan_brand_count", "id_brand", "nama"),  # Customer count by brand
        Index("idx_pelanggan_installation_trends", "tgl_instalasi", "id_brand"),  # Growth trends
        Index("idx_pelanggan_brand_location", "id_brand", "alamat"),  # Brand location distribution
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    no_ktp: Mapped[str] = mapped_column(String(191))  # Index sudah ada di composite idx_pelanggan_ktp_email
    nama: Mapped[str] = mapped_column(String(191))  # Index sudah ada di composite idx_pelanggan_nama_alamat
    alamat: Mapped[str] = mapped_column(String(191))  # Index sudah ada di composite idx_pelanggan_nama_alamat
    alamat_custom: Mapped[str | None] = mapped_column(String(191))
    alamat_2: Mapped[str | None] = mapped_column(Text)
    tgl_instalasi: Mapped[Date | None] = mapped_column(Date)  # Index sudah ada di composite idx_pelanggan_install_date
    blok: Mapped[str] = mapped_column(String(191))  # Index sudah ada di composite indexes
    unit: Mapped[str] = mapped_column(String(191))  # Index sudah ada di composite indexes
    no_telp: Mapped[str] = mapped_column(String(191))  # Tidak perlu index, jarang diquery sendirian
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True)  # Pertahankan unique index untuk validasi email
    id_brand: Mapped[str | None] = mapped_column(
        ForeignKey("harga_layanan.id_brand")
    )  # Index sudah ada di composite idx_pelanggan_brand_status
    layanan: Mapped[str | None] = mapped_column(String(191))  # Index sudah ada di composite idx_pelanggan_brand_status
    brand_default: Mapped[str | None] = mapped_column(String(191))
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # --- TAMBAHAN PENTING ---
    mikrotik_server_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("mikrotik_servers.id")
    )  # Tidak perlu index tambahan, foreign key index otomatis dibuat oleh database
    mikrotik_server: Mapped[Optional["MikrotikServer"]] = relationship("MikrotikServer", back_populates="pelanggan")
    # --- AKHIR TAMBAHAN ---

    # Relationships
    data_teknis: Mapped["DataTeknis"] = relationship(
        "DataTeknis", back_populates="pelanggan", uselist=False, cascade="all, delete-orphan"
    )
    langganan: Mapped[list["Langganan"]] = relationship("Langganan", back_populates="pelanggan")
    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="pelanggan")
    harga_layanan: Mapped["HargaLayanan"] = relationship("HargaLayanan", foreign_keys=[id_brand])
    # Tambahkan relasi ke inventory items
    inventory_items: Mapped[list["InventoryItem"]] = relationship("InventoryItem", back_populates="pelanggan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
