from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base

if TYPE_CHECKING:
    from .user import User


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    # Tambahkan index untuk query yang sering digunakan
    __table_args__ = (
        Index("idx_token_blacklist_jti", "jti"),
        Index("idx_token_blacklist_user_id", "user_id"),
        Index("idx_token_blacklist_expires_at", "expires_at"),
        Index("idx_token_blacklist_created_at", "created_at"),
        Index("idx_token_blacklist_token_type", "token_type"),
        Index("idx_token_blacklist_revoked", "revoked"),
        Index("idx_token_blacklist_revoked_at", "revoked_at"),
        Index("idx_token_blacklist_user_type", "user_id", "token_type"),
        Index("idx_token_blacklist_expires_revoked", "expires_at", "revoked"),
        Index("idx_token_blacklist_created_revoked", "created_at", "revoked"),
        Index("idx_token_blacklist_user_expires", "user_id", "expires_at"),
        Index("idx_token_blacklist_type_revoked", "token_type", "revoked"),
        Index("idx_token_blacklist_jti_revoked", "jti", "revoked"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    jti: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # JWT ID (UUID)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_type: Mapped[str] = mapped_column(String(50), index=True)  # 'access' atau 'refresh'
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    revoked: Mapped[bool] = mapped_column(default=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    # Relationship
    user = relationship("User", back_populates="blacklisted_tokens")

    def __repr__(self) -> str:
        return f"<TokenBlacklist(id={self.id}, jti='{self.jti}', user_id={self.user_id}, token_type='{self.token_type}', expires_at='{self.expires_at}')>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "jti": self.jti,
            "user_id": self.user_id,
            "token_type": self.token_type,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "revoked_reason": self.revoked_reason,
        }

    @classmethod
    def is_jti_blacklisted(cls, db, jti: str) -> bool:
        """Check if a JWT ID is blacklisted"""
        # Ini akan diimplementasikan di service layer
        return False

    @classmethod
    def blacklist_token(cls, db, jti: str, user_id: int, token_type: str, expires_at: datetime, reason: str | None = None) -> None:
        """Add a token to the blacklist"""
        # Ini akan diimplementasikan di service layer
        pass
