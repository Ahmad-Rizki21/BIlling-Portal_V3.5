import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ====================================================================
# --- BAGIAN YANG DIUBAH / DITAMBAHKAN ---
# ====================================================================

# 1. Tambahkan path root proyek agar Python bisa menemukan modul 'app'
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))

# 2. Impor 'Base' dari file database Anda
from app.database import Base

# 3. Impor SEMUA kelas model Anda secara eksplisit di sini.
#    Ini akan "mendaftarkan" semua tabel Anda ke 'Base.metadata'.
from app.models.data_teknis import DataTeknis
from app.models.harga_layanan import HargaLayanan
from app.models.invoice import Invoice
from app.models.langganan import Langganan
from app.models.mikrotik_server import MikrotikServer
from app.models.paket_layanan import PaketLayanan
from app.models.pelanggan import Pelanggan
from app.models.role import Role, role_has_permissions
from app.models.permission import Permission
from app.models.user import User
from app.models.sk import SK
from app.models.olt import OLT
from app.models.odp import ODP
from app.models.system_setting import SystemSetting

from app.models.inventory_item_type import InventoryItemType
from app.models.inventory_status import InventoryStatus
from app.models.inventory_item import InventoryItem
from app.models.inventory_history import InventoryHistory

from app.models.trouble_ticket import TroubleTicket, TicketHistory

# ====================================================================


# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Atur target_metadata DI SINI, SETELAH semua model diimpor ---
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
