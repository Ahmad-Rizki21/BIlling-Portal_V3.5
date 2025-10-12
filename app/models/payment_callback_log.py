from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, BigInteger, func, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class PaymentCallbackLog(Base):
    __tablename__ = "payment_callback_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    xendit_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    callback_data: Mapped[str | None] = mapped_column(String(1000), nullable=True)  # ringkas data callback
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # PAID, EXPIRED, dll
    processed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Tambahkan indeks untuk optimasi pencarian
    __table_args__ = (
        Index("idx_callback_log_xendit_id", "xendit_id"),
        Index("idx_callback_log_external_id", "external_id"),
        Index("idx_callback_log_idempotency_key", "idempotency_key"),
        Index("idx_callback_log_status", "status"),
    )

    def __repr__(self):
        return f"<PaymentCallbackLog(id={self.id}, xendit_id='{self.xendit_id}', external_id='{self.external_id}', status='{self.status}')>"
