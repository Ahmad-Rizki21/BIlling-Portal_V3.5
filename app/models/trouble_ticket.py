# ====================================================================
# MODEL TROUBLE TICKET - CUSTOMER SUPPORT MANAGEMENT
# ====================================================================
# Model ini mendefinisikan sistem trouble ticket untuk mengelola laporan
# masalah dari pelanggan layanan internet FTTH.
#
# Hubungan dengan tabel lain:
# - pelanggan      : Customer yang buat ticket ini
# - data_teknis    : Data teknis terkait masalah ini
# - users          : User/team yang ditugaskan menangani ticket
#
# Status Flow:
# - open -> in_progress -> resolved -> closed
# - open -> pending_customer -> in_progress -> ...
# - open -> pending_vendor -> in_progress -> ...
#
# Prioritas Level:
# - critical : Seluruh area down / emergency
# - high     : Pelanggan VIP / bisnis terganggu
# - medium   : Masalah koneksi individual
# - low      : Minor issues / pertanyaan
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from datetime import datetime
from sqlalchemy import BigInteger, ForeignKey, String, Text, DateTime, func, Column, Index, Integer, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

# Import Base dengan type annotation yang benar untuk mypy
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .pelanggan import Pelanggan
    from .data_teknis import DataTeknis
    from .user import User


class TicketStatus(enum.Enum):
    """
    Enum untuk status trouble ticket - Alur kerja ticket management.
    Ini mendefinisikan tahapan dari laporan masalah sampe solved.
    """
    OPEN = "open"                      # Ticket baru dibuat, belum ditangani
    IN_PROGRESS = "in_progress"        # Sedang ditangani oleh teknisi/support
    PENDING_CUSTOMER = "pending_customer"  # Menunggu konfirmasi dari pelanggan
    PENDING_VENDOR = "pending_vendor"  # Menunggu pihak ketiga/vendor
    RESOLVED = "resolved"              # Masalah sudah solved
    CLOSED = "closed"                  # Ticket ditutup (final state)
    CANCELLED = "cancelled"            # Ticket dibatalkan


class TicketPriority(enum.Enum):
    """
    Enum untuk prioritas trouble ticket - Level urgency masalah.
    Ini menentukan seberapa cepat ticket harus ditangani.
    """
    LOW = "low"          # Prioritas rendah - bisa ditangani nanti
    MEDIUM = "medium"    # Prioritas sedang - normal response time
    HIGH = "high"        # Prioritas tinggi - perlu cepat ditangani
    CRITICAL = "critical"  # Prioritas kritis - emergency response


class TicketCategory(enum.Enum):
    """
    Enum untuk kategori masalah - Jenis masalah yang dilaporkan.
    Ini membantu klasifikasi dan routing ke tim yang tepat.
    """
    NO_CONNECTION = "no_connection"        # Tidak ada koneksi sama sekali
    SLOW_CONNECTION = "slow_connection"    # Koneksi lambat
    INTERMITTENT = "intermittent"          # Koneksi putus-nyambung
    HARDWARE_ISSUE = "hardware_issue"      # Masalah hardware (router, etc)
    CABLE_ISSUE = "cable_issue"            # Masalah kabel fiber
    ONU_ISSUE = "onu_issue"                # Masalah device ONU di pelanggan
    OLT_ISSUE = "olt_issue"                # Masalah device OLT pusat
    MIKROTIK_ISSUE = "mikrotik_issue"      # Masalah konfigurasi Mikrotik
    OTHER = "other"                        # Masalah lain-lain


class TroubleTicket(Base):
    __tablename__ = "trouble_ticket"

    # OPTIMIZED index strategy untuk performa query trouble ticket
    __table_args__ = (
        # CORE indexes untuk query kritis
        Index("idx_ticket_pelanggan_status", "pelanggan_id", "status"),  # Customer ticket tracking
        Index("idx_ticket_status_priority", "status", "priority"),  # Priority queue
        Index("idx_ticket_created_date", "created_at"),  # Timeline tracking
        Index("idx_ticket_assigned_to", "assigned_to"),  # Workload distribution
        Index("idx_ticket_category_status", "category", "status"),  # Category analytics
        # COMPOSITE indexes untuk reporting dan analytics
        Index("idx_ticket_customer_timeline", "pelanggan_id", "created_at", "status"),
        Index("idx_ticket_priority_created", "priority", "created_at"),
        Index("idx_ticket_resolution_time", "resolved_at", "created_at"),
        Index("idx_ticket_downtime_calculation", "pelanggan_id", "downtime_start", "downtime_end"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign keys
    pelanggan_id: Mapped[int] = mapped_column(ForeignKey("pelanggan.id"), index=True)
    data_teknis_id: Mapped[int | None] = mapped_column(ForeignKey("data_teknis.id"), index=True)

    # Ticket information
    ticket_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[str] = mapped_column(Text)

    # Classification
    category: Mapped[TicketCategory] = mapped_column(Enum(TicketCategory), index=True)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority), index=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)

    # Downtime tracking
    downtime_start: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    downtime_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    total_downtime_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    # Assignment and resolution
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Customer communication
    customer_notified: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_customer_contact: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Evidence tracking
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)

    # Relationships
    pelanggan: Mapped["Pelanggan"] = relationship(back_populates="trouble_tickets")
    data_teknis: Mapped["DataTeknis"] = relationship(back_populates="trouble_tickets")
    assigned_user: Mapped["User"] = relationship(foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<TroubleTicket(id={self.id}, ticket_number={self.ticket_number}, status={self.status.value})>"

    def calculate_downtime_minutes(self) -> int:
        """Hitung downtime dalam menit"""
        if not self.downtime_start:
            return 0

        end_time = self.downtime_end or datetime.now()
        downtime = end_time - self.downtime_start
        return int(downtime.total_seconds() / 60)

    def update_downtime(self):
        """Update total downtime berdasarkan start dan end time"""
        self.total_downtime_minutes = self.calculate_downtime_minutes()

    def to_dict(self):
        """Convert ke dictionary untuk API response"""
        return {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "pelanggan_id": self.pelanggan_id,
            "data_teknis_id": self.data_teknis_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "downtime_start": self.downtime_start.isoformat() if self.downtime_start else None,
            "downtime_end": self.downtime_end.isoformat() if self.downtime_end else None,
            "total_downtime_minutes": self.total_downtime_minutes,
            "assigned_to": self.assigned_to,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "customer_notified": self.customer_notified,
            "last_customer_contact": self.last_customer_contact.isoformat() if self.last_customer_contact else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TicketHistory(Base):
    """Model untuk tracking perubahan status ticket"""
    __tablename__ = "ticket_history"

    __table_args__ = (
        Index("idx_history_ticket_time", "ticket_id", "created_at"),
        Index("idx_history_ticket_status", "ticket_id", "old_status", "new_status"),
        Index("idx_history_user", "changed_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("trouble_ticket.id"), index=True)

    # Status change tracking
    old_status: Mapped[TicketStatus | None] = mapped_column(Enum(TicketStatus), nullable=True)
    new_status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus))

    # Change information
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Relationships
    ticket: Mapped["TroubleTicket"] = relationship(back_populates="history")
    changed_user: Mapped["User"] = relationship(foreign_keys=[changed_by])


class ActionTaken(Base):
    """Model untuk tracking aksi yang diambil pada ticket"""
    __tablename__ = "action_taken"

    __table_args__ = (
        Index("idx_action_taken_ticket_time", "ticket_id", "created_at"),
        Index("idx_action_taken_user", "taken_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("trouble_ticket.id"), index=True)

    # Action information
    action_description: Mapped[str] = mapped_column(Text)
    summary_problem: Mapped[str] = mapped_column(Text)
    summary_action: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array string untuk multiple files
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Change information
    taken_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Relationships
    ticket: Mapped["TroubleTicket"] = relationship(back_populates="actions_taken")
    taken_user: Mapped["User"] = relationship(foreign_keys=[taken_by])

# Add relationship to existing models
# These will be added to the respective model files
TroubleTicket.history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan")
TroubleTicket.actions_taken = relationship("ActionTaken", back_populates="ticket", cascade="all, delete-orphan")