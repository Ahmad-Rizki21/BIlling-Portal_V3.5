from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base
from datetime import datetime


class SystemLog(Base):
    __tablename__ = "system_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    level: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
