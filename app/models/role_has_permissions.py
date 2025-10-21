from sqlalchemy import Table, Column, ForeignKey, BigInteger
# Import Base dengan type annotation yang benar untuk mypy
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase as Base
else:
    from ..database import Base

# Ini bukan kelas Model, tetapi definisi tabel langsung untuk relasi many-to-many.
# SQLAlchemy akan menggunakan objek ini untuk mengetahui bagaimana cara
# menghubungkan Role dan Permission.
role_has_permissions = Table(
    "role_has_permissions",
    Base.metadata,
    Column("permission_id", BigInteger, ForeignKey("permissions.id"), primary_key=True),
    Column("role_id", BigInteger, ForeignKey("roles.id"), primary_key=True),
)
