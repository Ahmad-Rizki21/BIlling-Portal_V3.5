# ====================================================================
# MODEL PELANGGAN - CUSTOMER DATA MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel pelanggan untuk menyimpan data customer
# dari layanan internet FTTH (Fiber To The Home).
#
# Hubungan dengan tabel lain:
# - data_teknis      : Informasi teknis koneksi internet
# - langganan        : Data langganan aktif pelanggan
# - invoices         : Tagihan/invoice pelanggan
# - harga_layanan    : Brand/provider yang dipake pelanggan
# - mikrotik_server  : Server yang nangani koneksi pelanggan
# - inventory_items  : Barang yang dipake/dikasih ke pelanggan
# - trouble_tickets  : Laporan masalah dari pelanggan
# ====================================================================

from __future__ import annotations
from sqlalchemy import BigInteger, String, Date, Text, ForeignKey, Column, Integer, Index, DateTime, func
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
    from .data_teknis import DataTeknis          # Data teknis koneksi
    from .langganan import Langganan            # Data langganan aktif
    from .invoice import Invoice                # Tagihan pelanggan
    from .harga_layanan import HargaLayanan     # Brand/provider
    from .mikrotik_server import MikrotikServer # Server Mikrotik
    from .inventory_item import InventoryItem   # Inventory items
    from .trouble_ticket import TroubleTicket   # Trouble tickets


class Pelanggan(Base):
    """
    Model tabel Pelanggan - menyimpan semua data customer/pelanggan.
    Ini adalah tabel utama yang nyambung ke hampir semua tabel lain.
    """
    __tablename__ = "pelanggan"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR PERFORMANCE
    # ====================================================================
    # Index strategy yang dioptimasi buat query yang sering dipake.
    # Total: 8 indexes buat balance antara performance dan storage.
    __table_args__ = (
        # Index buat query CORE yang sering dipake sehari-hari
        Index("idx_pelanggan_nama_alamat", "nama", "alamat"),        # Search pelanggan by nama & alamat
        Index("idx_pelanggan_blok_unit", "blok", "unit"),            # Pencarian lokasi perumahan
        Index("idx_pelanggan_brand_status", "id_brand", "layanan"),  # Filter brand & tipe layanan
        Index("idx_pelanggan_ktp_email", "no_ktp", "email"),         # Validasi unik KTP & email

        # Index buat PERFORMANCE dashboard dan reporting
        Index("idx_pelanggan_brand_count", "id_brand", "nama"),      # Hitung jumlah pelanggan per brand
        Index("idx_pelanggan_installation_trends", "tgl_instalasi", "id_brand"),  # Analisis pertumbuhan
        Index("idx_pelanggan_brand_location", "id_brand", "alamat"), # Distribusi pelanggan per lokasi
    )

    # ====================================================================
    # FIELD DEFINITIONS - DATA PELANGGAN
    # ====================================================================

    # Primary Key - ID unik buat setiap pelanggan
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Data Identitas Pelanggan
    no_ktp: Mapped[str] = mapped_column(String(191))          # Nomor KTP untuk verifikasi (index di composite)
    nama: Mapped[str] = mapped_column(String(191))            # Nama lengkap pelanggan (index di composite)
    alamat: Mapped[str] = mapped_column(String(191))          # Alamat utama (index di composite)
    alamat_custom: Mapped[str | None] = mapped_column(String(191))  # Alamat custom/keterangan tambahan
    alamat_2: Mapped[str | None] = mapped_column(Text)        # Alamat lengkap format teks panjang
    tgl_instalasi: Mapped[Date | None] = mapped_column(Date)  # Tanggal instalasi layanan

    # Data Lokasi (Perumahan/Cluster)
    blok: Mapped[str] = mapped_column(String(191))            # Blok perumahan (index di composite)
    unit: Mapped[str] = mapped_column(String(191))            # Unit/nomor rumah (index di composite)

    # Data Kontak
    no_telp: Mapped[str] = mapped_column(String(191))          # Nomor telepon/HP
    email: Mapped[str] = mapped_column(String(191), unique=True, index=True)  # Email (unique untuk login)

    # Data Layanan & Brand
    id_brand: Mapped[str | None] = mapped_column(
        ForeignKey("harga_layanan.id_brand")
    )  # ID brand/provider (index di composite)
    layanan: Mapped[str | None] = mapped_column(String(191))   # Tipe layanan (index di composite)
    brand_default: Mapped[str | None] = mapped_column(String(191))  # Brand default/keterangan

    # Timestamps (otomatis diisi oleh database)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now())  # Waktu dibuat
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())  # Waktu diupdate

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
    # Tambahkan relasi ke trouble tickets
    trouble_tickets: Mapped[list["TroubleTicket"]] = relationship("TroubleTicket", back_populates="pelanggan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
