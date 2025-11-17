# ====================================================================
# MODEL LANGGANAN - SUBSCRIPTION MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel langganan untuk menyimpan data
# berlangganan aktif pelanggan pada paket layanan tertentu.
#
# Hubungan dengan tabel lain:
# - pelanggan         : Customer yang punya langganan
# - paket_layanan     : Paket layanan yang diambil pelanggan
# - invoices          : Tagihan yang terkait dengan langganan ini
#
# Status Langganan:
# - aktif             : Langganan aktif dan berjalan normal
# - nonaktif          : Langganan berhenti/dinonaktifkan
# - suspend           : Langganan ditangguhkan (biasanya karena tunggakan)
# - pending           : Menunggu aktivasi
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import date, datetime
from sqlalchemy import BigInteger, ForeignKey, Date, String, func, Numeric, Column, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column

# Import Base dengan type annotation yang benar buat mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Import models buat relationship (dengan TYPE_CHECKING buat prevent circular import)
if TYPE_CHECKING:
    from .pelanggan import Pelanggan        # Data pelanggan
    from .paket_layanan import PaketLayanan  # Data paket layanan


class Langganan(Base):
    """
    Model tabel Langganan - menyimpan data langganan aktif pelanggan.
    Ini adalah tabel penghubung antara pelanggan dan paket layanan.
    """
    __tablename__ = "langganan"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR BILLING PERFORMANCE
    # ====================================================================
    # Index strategy yang dioptimasi buat query billing dan dashboard.
    # Total: 10 indexes buat balance antara performance query dan storage.

    __table_args__ = (
        # Index buat query CORE yang sering dipake sehari-hari
        Index("idx_langganan_customer_status", "pelanggan_id", "status"),        # Dashboard pelanggan
        Index("idx_langganan_package_status", "paket_layanan_id", "status"),     # Analisis paket
        Index("idx_langganan_due_date", "status", "tgl_jatuh_tempo"),           # Tracking jatuh tempo
        Index(
            "idx_langganan_subscription_dates", "tgl_mulai_langganan", "tgl_jatuh_tempo", "tgl_berhenti"
        ),  # Siklus hidup langganan

        # Index buat PERFORMANCE dashboard dan reporting
        Index("idx_langganan_active_subscriptions", "status", "paket_layanan_id"),     # Pelanggan aktif per paket
        Index("idx_langganan_revenue_tracking", "status", "harga_awal", "tgl_jatuh_tempo"),  # Tracking pendapatan
        Index("idx_langganan_payment_analysis", "metode_pembayaran", "status", "tgl_jatuh_tempo"),  # Analisis pembayaran

        # Composite foreign key indexes buat query join performance
        Index("idx_langganan_customer_package", "pelanggan_id", "paket_layanan_id", "status"),  # Analisis pelanggan-paket
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
    alasan_berhenti: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Alasan berhenti opsional
    status_modem: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # Status modem (Terpasang/Diambil)
    whatsapp_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # Status WhatsApp (sent/pending)
    last_whatsapp_sent: Mapped[datetime | None] = mapped_column(nullable=True, index=True)  # Terakhir kali WhatsApp dikirim
    created_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime | None] = mapped_column(server_default=func.now(), onupdate=func.now(), index=True)

    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="langganan")
    paket_layanan: Mapped["PaketLayanan"] = relationship(back_populates="langganan")
