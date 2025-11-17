from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime

from sqlalchemy import String, Integer, Text, func, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base


class SyaratKetentuan(Base):
    __tablename__ = "syarat_ketentuan"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    judul: Mapped[str] = mapped_column(String(255), nullable=False)
    konten: Mapped[str] = mapped_column(Text, nullable=False)  # TEXT type
    tipe: Mapped[str] = mapped_column(String(50), server_default=("'Ketentuan'"), nullable=True)
    versi: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Tambahkan indeks untuk optimasi
    __table_args__ = (
        Index("ix_syarat_ketentuan_id", "id"),
    )

    def __repr__(self):
        return f"<SyaratKetentuan(id={self.id}, judul='{self.judul}', tipe='{self.tipe}')>"