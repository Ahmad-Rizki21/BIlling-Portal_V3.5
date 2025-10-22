# ====================================================================
# MODEL PAKET LAYANAN - INTERNET PACKAGE MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel paket_layanan untuk menyimpan semua
# paket-paket internet yang ditawarkan ke pelanggan.
#
# Hubungan dengan tabel lain:
# - harga_layanan : Brand/provider yang menawarkan paket ini
# - langganan    : Pelanggan yang berlangganan paket ini
#
# Contoh paket:
# - "10 Mbps Premium" - Kecepatan 10 Mbps dengan harga tertentu
# - "50 Mbps Ultimate" - Kecepatan 50 Mbps untuk heavy user
# - "100 Mbps Business" - Kecepatan tinggi untuk kebutuhan bisnis
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .harga_layanan import HargaLayanan
    from .langganan import Langganan


class PaketLayanan(Base):
    """
    Model tabel PaketLayanan - nyimpen semua paket internet yang dijual.
    Ini adalah master data dari semua layanan yang bisa dipilih pelanggan.
    """
    __tablename__ = "paket_layanan"

    # ====================================================================
    # FIELD DEFINITIONS - DATA PAKET LAYANAN
    # ====================================================================

    # Primary Key - ID unik buat setiap paket layanan
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Foreign Key ke Brand/Provider
    id_brand: Mapped[str] = mapped_column(ForeignKey("harga_layanan.id_brand"), nullable=False)  # Brand/provider

    # Data Paket
    nama_paket: Mapped[str] = mapped_column(String(191), nullable=False)  # Nama paket (contoh: "10 Mbps Premium")
    kecepatan: Mapped[int] = mapped_column(nullable=False)               # Kecepatan internet dalam Mbps
    harga: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False) # Harga paket dalam Rupiah

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke HargaLayanan - Brand/provider yang menawarkan paket ini
    # Satu brand bisa punya banyak paket dengan kecepatan dan harga berbeda
    harga_layanan: Mapped["HargaLayanan"] = relationship(back_populates="paket_layanan")

    # Relasi ke Langganan - Semua pelanggan yang ambil paket ini
    # Satu paket bisa dipake oleh banyak pelanggan
    langganan: Mapped[list["Langganan"]] = relationship(back_populates="paket_layanan")
