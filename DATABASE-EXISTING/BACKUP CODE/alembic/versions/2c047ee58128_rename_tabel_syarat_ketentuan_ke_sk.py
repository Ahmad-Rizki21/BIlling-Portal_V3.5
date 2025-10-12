"""Rename tabel syarat_ketentuan ke sk

Revision ID: 2c047ee58128
Revises: 4cc22aad24ea
Create Date: 2025-08-18 20:30:34.018663

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2c047ee58128'
down_revision: Union[str, Sequence[str], None] = '4cc22aad24ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### Perintah yang benar untuk mengganti nama tabel ###
    op.rename_table('syarat_ketentuan', 'sk')


def downgrade() -> None:
    """Downgrade schema."""
    # ### Perintah yang benar untuk mengembalikan nama tabel ###
    op.rename_table('sk', 'syarat_ketentuan')