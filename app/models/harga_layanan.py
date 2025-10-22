# ====================================================================
# MODEL HARGA LAYANAN - BRAND/PROVIDER MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel harga_layanan untuk menyimpan data
# brand/provider layanan internet dan konfigurasi pajaknya.
#
# Hubungan dengan tabel lain:
# - pelanggan      : Customer yang menggunakan brand ini
# - paket_layanan  : Paket-paket yang ditawarkan oleh brand ini
#
# Contoh brand:
# - "JAKINET" - Provider utama dengan pajak 11%
# - "INDIHOME" - Provider alternatif dengan pajak berbeda
# - "MYREPUBLIK" - Provider lain dengan konfigurasi khusus
# ====================================================================

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
    from .paket_layanan import PaketLayanan  # Import buat relasi ke paket layanan


class HargaLayanan(Base):
    """
    Model tabel HargaLayanan - nyimpen data brand/provider layanan.
    Ini adalah master data dari semua provider yang bekerja sama dengan kita.
    """
    __tablename__ = "harga_layanan"

    # ====================================================================
    # FIELD DEFINITIONS - DATA BRAND/PROVIDER
    # ====================================================================

    # Primary Key - ID unik buat setiap brand/provider
    id_brand: Mapped[str] = mapped_column(String(191), primary_key=True)  # Kode unik brand (contoh: "JAKINET")

    # Data Brand
    brand: Mapped[str] = mapped_column(String(191), nullable=False)       # Nama brand/provider yang ditampilkan ke user
    pajak: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)  # Persentase pajak (contoh: 11.00)

    # Konfigurasi Pembayaran - Dipake buat integrasi payment gateway
    xendit_key_name: Mapped[str] = mapped_column(String(50), default="JAKINET", nullable=False)  # Key name buat Xendit API

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Pelanggan - Semua customer yang pake brand ini
    # Satu brand bisa dipake oleh banyak pelanggan
    pelanggan: Mapped[List["Pelanggan"]] = relationship(back_populates="harga_layanan", foreign_keys="[Pelanggan.id_brand]")

    # Relasi ke PaketLayanan - Semua paket yang ditawarkan oleh brand ini
    # Satu brand biasanya punya beberapa paket dengan kecepatan dan harga berbeda
    paket_layanan: Mapped[List["PaketLayanan"]] = relationship(back_populates="harga_layanan")
