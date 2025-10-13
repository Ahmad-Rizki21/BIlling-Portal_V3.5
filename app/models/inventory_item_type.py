from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base
from sqlalchemy import String


class InventoryItemType(Base):
    __tablename__ = "inventory_item_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
