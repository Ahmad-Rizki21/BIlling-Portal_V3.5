# Jadikan ini baris paling pertama di file Anda
from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base

if TYPE_CHECKING:
    from .olt import OLT
    from .data_teknis import DataTeknis

class ODP(Base):
    __tablename__ = "odp"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    kode_odp: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    alamat: Mapped[str | None] = mapped_column(String(255))
    kapasitas_port: Mapped[int] = mapped_column(Integer, default=8)

    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    parent_odp_id: Mapped[int | None] = mapped_column(ForeignKey("odp.id"), nullable=True)
    # Relasi untuk mendapatkan 'anak' dari sebuah ODP
    child_odps: Mapped[List["ODP"]] = relationship("ODP", back_populates="parent_odp")
    # Relasi untuk mendapatkan 'induk' dari sebuah ODP
    parent_odp: Mapped["ODP"] = relationship("ODP", remote_side=[id], back_populates="child_odps")

    # Relasi ke OLT
    olt_id: Mapped[int] = mapped_column(ForeignKey("olt.id"))
    olt: Mapped["OLT"] = relationship(back_populates="odps")


    # Relasi ke DataTeknis (one-to-many: satu ODP punya banyak data teknis)
    data_teknis: Mapped[List["DataTeknis"]] = relationship(back_populates="odp")
    