from sqlalchemy.orm import Mapped, mapped_column
# Import Base dengan type annotation yang benar untuk mypy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base
from sqlalchemy import String


class InventoryItemType(Base):
    __tablename__ = "inventory_item_types"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
