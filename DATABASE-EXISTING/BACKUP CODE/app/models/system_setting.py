# REVISI: Tidak ada perubahan, kode sudah benar.

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: Mapped[int] = mapped_column(primary_key=True)
    setting_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    setting_value: Mapped[str] = mapped_column(String(500), nullable=True)