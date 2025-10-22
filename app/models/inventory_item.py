# ====================================================================
# MODEL INVENTORY ITEM - EQUIPMENT MANAGEMENT
# ====================================================================
# Model ini mendefinisikan tabel inventory_items untuk menyimpan data
# barang-barang inventaris seperti ONU, router, kabel, dll.
#
# Hubungan dengan tabel lain:
# - inventory_item_type : Tipe/kategori barang ini
# - inventory_status    : Status barang (available, assigned, broken, etc)
# - pelanggan          : Pelanggan yang menggunakan barang ini (jika assigned)
#
# Status Flow:
# - available -> assigned -> returned -> available
# - available -> assigned -> broken -> repair -> available
# - available -> lost (end of lifecycle)
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Date, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Import buat relationship
if TYPE_CHECKING:
    from .inventory_item_type import InventoryItemType
    from .inventory_status import InventoryStatus
    from .pelanggan import Pelanggan


class InventoryItem(Base):
    """
    Model tabel InventoryItem - nyimpen semua data barang inventaris.
    Ini buat tracking peralatan yang dipake buat instalasi dan maintenance.
    """
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
