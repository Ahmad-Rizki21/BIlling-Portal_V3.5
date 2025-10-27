# ====================================================================
# MODEL TRAFFIC HISTORY - MONITORING DATA BANDWIDTH USAGE
# ====================================================================
# Model ini menyimpan data penggunaan bandwidth PPPoE user dari Mikrotik.
# Digunakan untuk monitoring real-time dan analisis historis.
#
# Data yang disimpan:
# - Traffic counters (rx/tx bytes) per user
# - Timestamp untuk tracking trend
# - Bandwidth calculation (Mbps)
# - Connection dengan data_teknis dan mikrotik_server
#
# Usage:
# - Real-time monitoring dashboard
# - Historical bandwidth analysis
# - Trend reporting
# - Alert threshold monitoring
# ====================================================================

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Column, String, Integer, BigInteger, Float, DateTime, Boolean, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

if TYPE_CHECKING:
    from .data_teknis import DataTeknis
    from .mikrotik_server import MikrotikServer


class TrafficHistory(Base):
    """
    Model tabel traffic_history - menyimpan data penggunaan bandwidth PPPoE user.
    Critical untuk monitoring network performance dan capacity planning.
    """
    __tablename__ = "traffic_history"

    # ====================================================================
    # DATABASE INDEXES - OPTIMIZED FOR TRAFFIC MONITORING
    # ====================================================================
    __table_args__ = (
        # Primary indexes untuk query traffic data
        Index("idx_traffic_timestamp", "timestamp"),  # Time-based queries
        Index("idx_traffic_data_teknis", "data_teknis_id"),  # User-based queries
        Index("idx_traffic_server", "mikrotik_server_id"),  # Server-based queries

        # Composite indexes untuk analytics queries
        Index("idx_traffic_user_time", "data_teknis_id", "timestamp"),  # User traffic history
        Index("idx_traffic_server_time", "mikrotik_server_id", "timestamp"),  # Server load
        Index("idx_traffic_pppoe_time", "username_pppoe", "timestamp"),  # PPPoE tracking

        # Performance indexes untuk dashboard queries
        Index("idx_traffic_latest", "is_latest", "timestamp"),  # Latest data queries
        Index("idx_traffic_bandwidth", "rx_mbps", "tx_mbps", "timestamp"),  # Bandwidth analysis
    )

    # ====================================================================
    # FIELD DEFINITIONS
    # ====================================================================

    # Primary Key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)

    # Foreign Keys
    data_teknis_id: Mapped[int] = mapped_column(ForeignKey("data_teknis.id"), index=True)
    mikrotik_server_id: Mapped[int] = mapped_column(ForeignKey("mikrotik_servers.id"), index=True)

    # PPPoE Identification
    username_pppoe: Mapped[str] = mapped_column(String(100), index=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True)  # Support IPv6

    # Traffic Counters (from Mikrotik)
    rx_bytes: Mapped[int] = mapped_column(BigInteger, default=0)  # Download bytes
    tx_bytes: Mapped[int] = mapped_column(BigInteger, default=0)  # Upload bytes
    rx_packets: Mapped[int] = mapped_column(BigInteger, default=0)  # Download packets
    tx_packets: Mapped[int] = mapped_column(BigInteger, default=0)  # Upload packets

    # Calculated Bandwidth (Mbps)
    rx_mbps: Mapped[float] = mapped_column(Float, default=0.0)  # Download Mbps
    tx_mbps: Mapped[float] = mapped_column(Float, default=0.0)  # Upload Mbps
    total_mbps: Mapped[float] = mapped_column(Float, default=0.0)  # Total Mbps

    # Connection Status
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, default=0)  # Connection uptime
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # Connection status

    # Metadata
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, index=True)  # Flag untuk latest data

    # ====================================================================
    # RELATIONSHIPS
    # ====================================================================

    data_teknis: Mapped[DataTeknis] = relationship(
        "DataTeknis",
        back_populates="traffic_history",
        lazy="joined"
    )

    mikrotik_server: Mapped[MikrotikServer] = relationship(
        "MikrotikServer",
        back_populates="traffic_history",
        lazy="joined"
    )

    # ====================================================================
    # UTILITY METHODS
    # ====================================================================

    def to_dict(self) -> dict:
        """Convert ke dictionary untuk API response."""
        return {
            "id": self.id,
            "data_teknis_id": self.data_teknis_id,
            "mikrotik_server_id": self.mikrotik_server_id,
            "username_pppoe": self.username_pppoe,
            "ip_address": self.ip_address,
            "rx_bytes": self.rx_bytes,
            "tx_bytes": self.tx_bytes,
            "rx_packets": self.rx_packets,
            "tx_packets": self.tx_packets,
            "rx_mbps": round(self.rx_mbps, 2),
            "tx_mbps": round(self.tx_mbps, 2),
            "total_mbps": round(self.total_mbps, 2),
            "uptime_seconds": self.uptime_seconds,
            "is_active": self.is_active,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "is_latest": self.is_latest,
            # Additional info from relationships
            "pelanggan_name": self.data_teknis.pelanggan.nama if self.data_teknis and self.data_teknis.pelanggan else None,
            "server_name": self.mikrotik_server.name if self.mikrotik_server else None,
        }

    @classmethod
    def format_bytes(cls, bytes_value: int) -> str:
        """Format bytes ke human readable format."""
        value = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0
        return f"{value:.2f} PB"

    @classmethod
    def calculate_mbps(cls, bytes_value: int, time_interval: int = 300) -> float:
        """Calculate Mbps dari bytes dan time interval (default 5 menit)."""
        if time_interval <= 0:
            return 0.0
        bits_per_second = (bytes_value * 8) / time_interval
        return bits_per_second / 1_000_000  # Convert to Mbps

    def get_uptime_formatted(self) -> str:
        """Format uptime ke human readable format."""
        if not self.uptime_seconds:
            return "0s"

        days = self.uptime_seconds // 86400
        hours = (self.uptime_seconds % 86400) // 3600
        minutes = (self.uptime_seconds % 3600) // 60
        seconds = self.uptime_seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)