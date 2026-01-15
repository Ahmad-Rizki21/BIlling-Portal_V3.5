"""
Instalasi Document Model
Untuk menyimpan foto-foto BA Instalasi (ODP before/after, ONU, speedtest, signature, dll)
"""
from datetime import datetime
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from ..database import Base


class InstalasiDocument(Base):
    __tablename__ = "instalasi_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pelanggan_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("pelanggan.id"), nullable=True, index=True)
    work_order_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("work_orders.id"), nullable=True, index=True)

    # Document type: photo_odp_before, photo_odp_after, photo_onu, photo_speedtest, signature_pelanggan, etc.
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # File information
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # Upload information
    uploaded_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Optional notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    # pelanggan = relationship("Pelanggan", back_populates="instalasi_documents")
    # work_order = relationship("WorkOrder", back_populates="instalasi_documents")
    # uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<InstalasiDocument(id={self.id}, type={self.document_type}, pelanggan_id={self.pelanggan_id})>"
