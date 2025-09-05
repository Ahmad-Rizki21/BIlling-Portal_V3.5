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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database import Base
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pelanggan import Pelanggan
class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    invoice_number: Mapped[str] = mapped_column(
        String(191), unique=True
    )  # Sesuai dengan UNIQUE KEY
    pelanggan_id: Mapped[int] = mapped_column(
        ForeignKey("pelanggan.id"), index=True
    )  # Ditambahkan index untuk performa
    id_pelanggan: Mapped[str] = mapped_column(String(255))
    brand: Mapped[str] = mapped_column(String(191))
    total_harga: Mapped[float] = mapped_column(Numeric(15, 2))
    no_telp: Mapped[str] = mapped_column(String(191))
    email: Mapped[str] = mapped_column(String(191))
    tgl_invoice: Mapped[Date] = mapped_column(Date)
    tgl_jatuh_tempo: Mapped[Date] = mapped_column(
        Date, index=True
    )  # Ditambahkan index untuk performa
    status_invoice: Mapped[str] = mapped_column(
        String(50), index=True
    )  # Ditambahkan index untuk performa
    payment_link: Mapped[str | None] = mapped_column(Text)
    metode_pembayaran: Mapped[str | None] = mapped_column(String(50))
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime)
    xendit_id: Mapped[str | None] = mapped_column(String(191))
    xendit_external_id: Mapped[str | None] = mapped_column(
        String(191), index=True
    )  # Ditambahkan index untuk performa
    paid_amount: Mapped[float | None] = mapped_column(Numeric(15, 2))
    paid_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)
    is_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP)

    # Relationship
    pelanggan = relationship("Pelanggan", back_populates="invoices")
