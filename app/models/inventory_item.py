# app/models/inventory_item.py

# --- 1. Pastikan import ini ada ---
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

# --- 2. Tambahkan blok TYPE_CHECKING untuk menghindari circular import ---
if TYPE_CHECKING:
    from .inventory_item_type import InventoryItemType
    from .inventory_status import InventoryStatus
    from .pelanggan import Pelanggan


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    serial_number: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    mac_address: Mapped[str | None] = mapped_column(String(255), unique=True)
    location: Mapped[str | None] = mapped_column(String(255))
    purchase_date: Mapped[Date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    item_type_id: Mapped[int] = mapped_column(ForeignKey("inventory_item_types.id"))
    status_id: Mapped[int] = mapped_column(ForeignKey("inventory_statuses.id"))
    pelanggan_id: Mapped[int | None] = mapped_column(ForeignKey("pelanggan.id"))

    # --- 3. TAMBAHKAN DUA BARIS RELATIONSHIP INI ▼▼▼ ---
    item_type: Mapped["InventoryItemType"] = relationship()
    status: Mapped["InventoryStatus"] = relationship()
    # Tambahkan relasi ke pelanggan
    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="inventory_items")
    # --- AKHIR BLOK TAMBAHAN ▲▲▲
