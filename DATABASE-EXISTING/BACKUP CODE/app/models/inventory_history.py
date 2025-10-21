from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from ..database import Base


class InventoryHistory(Base):
    __tablename__ = "inventory_history"
    id: Mapped[int] = mapped_column(primary_key=True)
    action: Mapped[str] = mapped_column(String(255))
    timestamp: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    
    item_id: Mapped[int] = mapped_column(ForeignKey("inventory_items.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))