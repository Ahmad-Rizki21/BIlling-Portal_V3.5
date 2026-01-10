"""
Model untuk tabel arsip invoice.
Digunakan untuk menyimpan data invoice lama yang jarang diakses
untuk mengurangi beban tabel invoices utama.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime
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
    from .pelanggan import Pelanggan # Tidak digunakan di arsip, tapi tetap bisa diimpor jika diperlukan


class InvoiceArchive(Base):
    """
    Model tabel InvoiceArchive - nyimpen data invoice historis.
    Struktur disamakan dengan Invoice utama untuk kemudahan migrasi dan pencarian.
    """
    __tablename__ = "invoices_archive"

    # Pastikan nama indeks berbeda jika dibutuhkan untuk menghindari konflik
    __table_args__ = (
        # Constraint untuk validasi data (jika relevan)
        CheckConstraint("pelanggan_id IS NOT NULL", name="ck_invoice_archive_pelanggan_id_not_null"),
        # Indeks bisa disesuaikan, mungkin tidak perlu semua untuk arsip
        Index("idx_archive_pelanggan_status", "pelanggan_id", "status_invoice"),  # Untuk pencarian pelanggan
        Index("idx_archive_status_tanggal", "status_invoice", "tgl_invoice"),     # Untuk laporan historis
        Index("idx_archive_tanggal", "tgl_invoice"),                              # Filter rentang waktu
        Index("idx_archive_invoice_number", "invoice_number"),                    # Cari berdasarkan nomor
    )

    # Field disalin dari model Invoice utama
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True, autoincrement=True) # Pastikan auto-increment

    # Data Identitas Invoice
    invoice_number: Mapped[str] = mapped_column(String(191), unique=True, index=True)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), nullable=False)  # Foreign key ke pelanggan - Harus nullable=False seperti di Invoice

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

    # Data Payment Gateway (Xendit Integration) - Mungkin sudah tidak relevan di arsip
    xendit_id: Mapped[str | None] = mapped_column(String(191))           # ID dari Xendit API
    xendit_external_id: Mapped[str | None] = mapped_column(String(191))  # External ID buat Xendit
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)  # Flag buat hindari duplicate processing

    # Retry System - Mungkin sudah tidak relevan di arsip
    xendit_retry_count: Mapped[int] = mapped_column(BigInteger, default=0)  # Jumlah retry yang sudah dilakukan
    xendit_last_retry: Mapped[datetime | None] = mapped_column(DateTime)   # Waktu retry terakhir
    xendit_error_message: Mapped[str | None] = mapped_column(Text)         # Error message terakhir
    xendit_status: Mapped[str] = mapped_column(String(50), default="pending")  # pending/processing/completed/failed

    # Invoice Type Tracking System
    invoice_type: Mapped[str] = mapped_column(String(50), default="manual")  # Jenis invoice (manual/automatic/reinvoice)

    # Reinvoice Tracking System
    is_reinvoice: Mapped[bool] = mapped_column(Boolean, default=False)     # Flag untuk menandai invoice reinvoice
    original_invoice_id: Mapped[int | None] = mapped_column(BigInteger)    # ID invoice asli yang direinvoice
    reinvoice_reason: Mapped[str | None] = mapped_column(String(255))      # Alasan reinvoice (expired/suspended/manual)

    # Timestamps
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())  # Waktu invoice dibuat
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )  # Waktu invoice diupdate
    # deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)  # Soft delete (jika diperlukan di arsip, atau biarkan NULL)

    # Relasi ke Pelanggan - Penting untuk search by name di Archive
    pelanggan: Mapped["Pelanggan"] = relationship("Pelanggan")

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_payment_link_status(self):
        """
        Mengembalikan status link pembayaran berdasarkan logika:
        - Jika invoice sudah lunas: "Lunas"
        - Jika hari ini <= tanggal 6 bulan berikutnya: "Belum Dibayar" (link aktif)
        - Jika hari ini >= tanggal 7 bulan berikutnya: "Expired" (link tidak aktif)
        """
        from datetime import date, timedelta, datetime

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

    @property
    def pelanggan_nama(self):
        """
        Property untuk mengambil nama pelanggan dari relasi.
        Memudahkan serialisasi ke schema tanpa lookup list di frontend.
        """
        return self.pelanggan.nama if self.pelanggan else None