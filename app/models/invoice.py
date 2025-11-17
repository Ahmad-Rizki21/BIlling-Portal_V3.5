# ====================================================================
# MODEL INVOICE - BILLING & PAYMENT MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel invoices untuk menyimpan semua data
# tagihan/invoice pelanggan layanan internet FTTH.
#
# Hubungan dengan tabel lain:
# - pelanggan : Customer yang punya invoice ini
#
# Status Invoice:
# - Belum Dibayar : Invoice baru yang belum dibayar pelanggan
# - Lunas        : Invoice yang sudah dibayar penuh
# - Expired      : Invoice yang melewati batas waktu pembayaran
# - Batal        : Invoice yang dibatalkan
#
# Payment Gateway Integration:
# - Xendit API untuk pembayaran online
# - Link pembayaran yang kadaluarsa otomatis
# - Callback system untuk update status pembayaran
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime, timedelta
from sqlalchemy import (
    BigInteger,
    String,
    Date,
    DateTime,
    Text,
    ForeignKey,
    Numeric,
    Boolean,
    func,
    TIMESTAMP,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan


class Invoice(Base):
    """
    Model tabel Invoice - nyimpen semua data tagihan pelanggan.
    Ini adalah tabel krusial buat sistem billing dan pembayaran.
    """
    __tablename__ = "invoices"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR BILLING PERFORMANCE
    # ====================================================================
    # Index strategy yang dioptimasi buat operasi billing dan dashboard finance.
    # Total: 10 indexes buat balance antara query performance dan write speed.
    # Dari 15+ index jadi 10 aja biar operasi invoice lebih cepat.
    __table_args__ = (
        # Constraint untuk validasi data
        CheckConstraint("pelanggan_id IS NOT NULL", name="ck_invoice_pelanggan_id_not_null"),  # Pastikan pelanggan_id tidak kosong

        # Index buat query CORE yang sering dipake finance team
        Index("idx_invoice_customer_status", "pelanggan_id", "status_invoice"),  # Dashboard pelanggan per status
        Index("idx_invoice_status_brand", "status_invoice", "brand"),              # Filter invoice berdasarkan brand
        Index("idx_invoice_date_range", "tgl_invoice", "tgl_jatuh_tempo"),        # Filter invoice berdasarkan tanggal
        Index("idx_invoice_payment_tracking", "status_invoice", "paid_at"),        # Tracking pembayaran

        # Index buat PERFORMANCE dashboard dan laporan keuangan
        Index("idx_invoice_revenue_analysis", "status_invoice", "tgl_invoice", "total_harga"),  # Analisis pendapatan
        Index("idx_invoice_late_payment", "paid_at", "tgl_jatuh_tempo"),                          # Analisis pembayaran terlambat
        Index("idx_invoice_brand_revenue", "brand", "tgl_invoice", "total_harga"),               # Laporan pendapatan per brand

        # Index buat INTEGRASI payment gateway
        Index("idx_invoice_xendit_lookup", "xendit_id", "status_invoice"),        # Lookup invoice dari Xendit callback
        Index("idx_invoice_number_lookup", "invoice_number", "status_invoice"),    # Search invoice by number
        Index("idx_invoice_payment_method", "metode_pembayaran", "status_invoice"), # Analisis metode pembayaran
    )

    # ====================================================================
    # FIELD DEFINITIONS - DATA INVOICE
    # ====================================================================

    # Primary Key - ID unik buat setiap invoice
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Data Identitas Invoice
    invoice_number: Mapped[str] = mapped_column(String(191), unique=True, index=True)  # Nomor invoice unik (contoh: "INV/2024/001")
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), nullable=False)  # Foreign key ke pelanggan

    # Data Pelanggan (Redundant buat performance & history)
    id_pelanggan: Mapped[str] = mapped_column(String(255))  # ID pelanggan (disimpan buat history)
    brand: Mapped[str] = mapped_column(String(191))        # Brand/provider (disimpan buat history)
    no_telp: Mapped[str] = mapped_column(String(191))      # Nomor telepon (buat notifikasi)
    email: Mapped[str] = mapped_column(String(191))        # Email (buat kirim invoice)

    # Data Tagihan
    total_harga: Mapped[float] = mapped_column(Numeric(15, 2))  # Total tagihan dalam Rupiah
    tgl_invoice: Mapped[Date] = mapped_column(Date)              # Tanggal pembuatan invoice
    tgl_jatuh_tempo: Mapped[Date] = mapped_column(Date)          # Tanggal jatuh tempo pembayaran
    status_invoice: Mapped[str] = mapped_column(String(50))      # Status invoice (Belum Dibayar/Lunas/Expired/Batal)

    # Data Pembayaran
    payment_link: Mapped[str | None] = mapped_column(Text)                # Link pembayaran dari Xendit
    metode_pembayaran: Mapped[str | None] = mapped_column(String(50))     # Metode pembayaran yang dipake
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime)        # Tanggal kadaluarsa link pembayaran
    paid_amount: Mapped[float | None] = mapped_column(Numeric(15, 2))    # Jumlah yang sudah dibayar
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)          # Waktu pembayaran dilakukan

    # Data Payment Gateway (Xendit Integration)
    xendit_id: Mapped[str | None] = mapped_column(String(191))           # ID dari Xendit API
    xendit_external_id: Mapped[str | None] = mapped_column(String(191))  # External ID buat Xendit
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag buat hindari duplicate processing

    # Retry System - Tracking Invoice Gagal
    xendit_retry_count: Mapped[int] = mapped_column(BigInteger, default=0)  # Jumlah retry yang sudah dilakukan
    xendit_last_retry: Mapped[datetime | None] = mapped_column(DateTime)   # Waktu retry terakhir
    xendit_error_message: Mapped[str | None] = mapped_column(Text)         # Error message terakhir
    xendit_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending/processing/completed/failed

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())  # Waktu invoice dibuat
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )  # Waktu invoice diupdate
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)  # Waktu invoice dihapus (soft delete)

    # ====================================================================
    # RELATIONSHIPS - HUBUNGAN TABEL
    # ====================================================================

    # Relasi ke Pelanggan - Customer yang punya invoice ini
    pelanggan = relationship("Pelanggan", back_populates="invoices")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_payment_link_status(self):
        """
        Mengembalikan status link pembayaran berdasarkan logika:
        - Jika invoice sudah lunas: "Lunas"
        - Jika hari ini <= tanggal 6 bulan berikutnya: "Belum Dibayar" (link aktif)
        - Jika hari ini >= tanggal 7 bulan berikutnya: "Expired" (link tidak aktif)
        """
        from datetime import date

        today = date.today()

        # Jika invoice sudah lunas
        if self.status_invoice == "Lunas":
            return "Lunas"

        # Jika invoice belum dibayar
        if self.status_invoice == "Belum Dibayar":
            # Hitung tanggal 6 bulan berikutnya dari invoice date
            # Convert SQLAlchemy Date ke Python date dengan aman
            try:
                # Approach 1: Coba convert langsung ke Python date
                invoice_date = date.fromisoformat(str(self.tgl_invoice))
            except:
                try:
                    # Approach 2: Gunakan datetime parsing
                    invoice_date = datetime.strptime(str(self.tgl_invoice), "%Y-%m-%d").date()
                except:
                    # Approach 3: Fallback ke default 10 hari
                    expiry_date = today + timedelta(days=10)
                    # Link aktif jika hari ini <= expiry_date (tanggal 6 atau sebelumnya)
                    if today <= expiry_date:
                        return "Belum Dibayar"
                    else:
                        return "Expired"

            # Sekarang invoice_date pasti Python date object yang valid
            if invoice_date.month == 12:
                expiry_date = date(invoice_date.year + 1, 1, 4)  # Link aktif sampai tanggal 4
            else:
                expiry_date = date(invoice_date.year, invoice_date.month + 1, 4)  # Link aktif sampai tanggal 4

            # Link aktif jika hari ini <= expiry_date (tanggal 4 atau sebelumnya)
            if today <= expiry_date:
                return "Belum Dibayar"
            else:
                # Link expired jika hari ini > expiry_date (tanggal 5 atau setelahnya)
                return "Expired"

        # Fallback ke status invoice yang ada
        return self.status_invoice

    @property
    def is_payment_link_active(self):
        """
        Mengembalikan True jika link pembayaran masih aktif.
        Link aktif jika:
        - Status invoice "Belum Dibayar"
        - Hari ini <= tanggal 4 bulan berikutnya (grace period sampai tanggal 4)
        """
        return self.get_payment_link_status() == "Belum Dibayar"

    @property
    def payment_link_status(self):
        """
        Property untuk status link pembayaran.
        """
        return self.get_payment_link_status()
