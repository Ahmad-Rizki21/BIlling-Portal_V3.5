from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from sqlalchemy import String


class InventoryStatus(Base):
    __tablename__ = "inventory_statuses"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

