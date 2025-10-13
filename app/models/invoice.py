# app/models/invoice.py - OPTIMIZED VERSION

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan


class Invoice(Base):
    __tablename__ = "invoices"

    # OPTIMIZED index strategy - Hanya index yang BENAR-BENAR PENTING
    # Total: 10 indexes (dari 15+) untuk balance performa read/write
    __table_args__ = (
        CheckConstraint("pelanggan_id IS NOT NULL", name="ck_invoice_pelanggan_id_not_null"),
        # CORE indexes untuk query kritis yang sering digunakan
        Index("idx_invoice_customer_status", "pelanggan_id", "status_invoice"),  # Customer dashboard
        Index("idx_invoice_status_brand", "status_invoice", "brand"),  # Dashboard filtering
        Index("idx_invoice_date_range", "tgl_invoice", "tgl_jatuh_tempo"),  # Date filtering
        Index("idx_invoice_payment_tracking", "status_invoice", "paid_at"),  # Payment tracking
        # PERFORMANCE indexes untuk dashboard revenue
        Index("idx_invoice_revenue_analysis", "status_invoice", "tgl_invoice", "total_harga"),  # Revenue dashboard
        Index("idx_invoice_late_payment", "paid_at", "tgl_jatuh_tempo"),  # Loyalty analysis
        Index("idx_invoice_brand_revenue", "brand", "tgl_invoice", "total_harga"),  # Brand reporting
        # INTEGRATION indexes untuk payment processing
        Index("idx_invoice_xendit_lookup", "xendit_id", "status_invoice"),  # Xendit callback
        Index("idx_invoice_number_lookup", "invoice_number", "status_invoice"),  # Invoice search
        Index("idx_invoice_payment_method", "metode_pembayaran", "status_invoice"),  # Payment analysis
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(191), unique=True, index=True)  # Unique index untuk invoice lookup
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), nullable=False)  # Foreign key index otomatis dibuat
    id_pelanggan: Mapped[str] = mapped_column(String(255))  # Tidak perlu index, jarang diquery
    brand: Mapped[str] = mapped_column(String(191))  # Sudah ada di composite index
    total_harga: Mapped[float] = mapped_column(Numeric(15, 2))  # Sudah ada di composite index
    no_telp: Mapped[str] = mapped_column(String(191))  # Tidak perlu index, jarang diquery
    email: Mapped[str] = mapped_column(String(191))  # Tidak perlu index, jarang diquery
    tgl_invoice: Mapped[Date] = mapped_column(Date)  # Sudah ada di composite index
    tgl_jatuh_tempo: Mapped[Date] = mapped_column(Date)  # Sudah ada di composite index
    status_invoice: Mapped[str] = mapped_column(String(50))  # Sudah ada di composite index
    payment_link: Mapped[str | None] = mapped_column(Text)  # Tidak perlu index
    metode_pembayaran: Mapped[str | None] = mapped_column(String(50))  # Sudah ada di composite index
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime)  # Tidak perlu index
    xendit_id: Mapped[str | None] = mapped_column(String(191))  # Sudah ada di composite index
    xendit_external_id: Mapped[str | None] = mapped_column(String(191))  # Tidak perlu index
    paid_amount: Mapped[float | None] = mapped_column(Numeric(15, 2))  # Tidak perlu index
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)  # Sudah ada di composite index
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)  # Tidak perlu index
    created_at: Mapped[datetime | None] = mapped_column(DateTime, server_default=func.now())  # Tidak perlu index
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )  # Tidak perlu index
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)  # Tidak perlu index

    # Relationship - TIDAK DIUBAH SAMA SEKALI!
    pelanggan = relationship("Pelanggan", back_populates="invoices")

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def get_payment_link_status(self) -> str:
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
                expiry_date = date(invoice_date.year + 1, 1, 6)
            else:
                expiry_date = date(invoice_date.year, invoice_date.month + 1, 6)

            # Link aktif jika hari ini <= expiry_date (tanggal 6 atau sebelumnya)
            if today <= expiry_date:
                return "Belum Dibayar"
            else:
                # Link expired jika hari ini > expiry_date (tanggal 7 atau setelahnya)
                return "Expired"

        # Fallback ke status invoice yang ada
        return self.status_invoice

    @property
    def is_payment_link_active(self) -> bool:
        """
        Mengembalikan True jika link pembayaran masih aktif.
        Link aktif jika:
        - Status invoice "Belum Dibayar"
        - Hari ini <= tanggal 6 bulan berikutnya
        """
        return self.get_payment_link_status() == "Belum Dibayar"

    @property
    def payment_link_status(self) -> str:
        """
        Property untuk status link pembayaran.
        """
        return self.get_payment_link_status()
