# app/models/langganan.py

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, Date, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .paket_layanan import PaketLayanan
    from .pelanggan import Pelanggan


class Langganan(Base):
    __tablename__ = "langganan"

    # OPTIMIZED index strategy - Hanya index yang BENAR-BENAR PENTING untuk performa
    # Total: 10 indexes (dari 16+) untuk balance performa read/write
    __table_args__ = (
        # CORE indexes untuk query kritis yang sering digunakan
        Index("idx_langganan_customer_status", "pelanggan_id", "status"),  # Customer dashboard
        Index("idx_langganan_package_status", "paket_layanan_id", "status"),  # Package analytics
        Index("idx_langganan_due_date", "status", "tgl_jatuh_tempo"),  # Due date tracking
        Index(
            "idx_langganan_subscription_dates", "tgl_mulai_langganan", "tgl_jatuh_tempo", "tgl_berhenti"
        ),  # Subscription lifecycle
        # PERFORMANCE indexes untuk dashboard dan reporting
        Index("idx_langganan_active_subscriptions", "status", "paket_layanan_id"),  # Active customers by package
        Index("idx_langganan_revenue_tracking", "status", "harga_awal", "tgl_jatuh_tempo"),  # Revenue tracking
        Index("idx_langganan_payment_analysis", "metode_pembayaran", "status", "tgl_jatuh_tempo"),  # Payment analysis
        # FOREIGN KEY indexes (otomatis dibuat tapi perlu composite untuk performance)
        Index("idx_langganan_customer_package", "pelanggan_id", "paket_layanan_id", "status"),  # Customer-package analysis
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), index=True)
    paket_layanan_id: Mapped[int] = mapped_column(ForeignKey("paket_layanan.id"), index=True)
    status: Mapped[str] = mapped_column(String(100), index=True)
    tgl_jatuh_tempo: Mapped[Date | None] = mapped_column(Date, index=True)
    tgl_invoice_terakhir: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # --- PASTIKAN HANYA BARIS YANG BENAR INI YANG ADA ---
    tgl_mulai_langganan = Column(Date, nullable=True, index=True)
    tgl_berhenti: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    metode_pembayaran: Mapped[str] = mapped_column(String(50), default="Otomatis", index=True)
    harga_awal: Mapped[float | None] = mapped_column(Numeric(15, 2), index=True)
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now(), index=True)

    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="langganan")
    paket_layanan: Mapped["PaketLayanan"] = relationship(back_populates="langganan")
