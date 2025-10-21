"""Gabungkan riwayat produksi

Revision ID: f7cbc8fae992
Revises: 395123925185, b68575008a99, b7d91180af7e
Create Date: 2025-09-05 02:43:14.960450

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f7cbc8fae992'
down_revision: Union[str, Sequence[str], None] = ('395123925185', 'b68575008a99', 'b7d91180af7e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
