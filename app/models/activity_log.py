# --- 1. Tambahkan import yang diperlukan ---
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, Text, DateTime, func, ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)  # <-- Tambahkan relationship
from ..database import Base
from datetime import datetime

# --- 2. Tambahkan blok TYPE_CHECKING untuk type hint ---
if TYPE_CHECKING:
    from .user import User


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[str | None] = mapped_column(Text)

    # --- 3. Tambahkan relasi ini ---
    # Ini memberitahu SQLAlchemy cara menghubungkan ActivityLog ke User
    user: Mapped["User"] = relationship(back_populates="activity_logs")
