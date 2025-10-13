# app/models/sk.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from ..database import Base


class SK(Base):
    __tablename__ = "syarat_ketentuan"

    id = Column(Integer, primary_key=True, index=True)
    judul = Column(String(255), nullable=False)
    konten = Column(Text, nullable=False)
    tipe = Column(String(50), default="Ketentuan")  # Tipe bisa "Ketentuan" atau "Pembaruan"
    versi = Column(String(50), nullable=True)  # Versi aplikasi, cth: "v2.1.0"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
