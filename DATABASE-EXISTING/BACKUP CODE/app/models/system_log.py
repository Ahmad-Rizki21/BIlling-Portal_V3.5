from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SystemLog(Base):
    __tablename__ = "system_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    level: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(Text)
