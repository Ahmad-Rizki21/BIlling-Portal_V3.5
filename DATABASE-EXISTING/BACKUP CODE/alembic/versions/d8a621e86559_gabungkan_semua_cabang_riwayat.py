"""Gabungkan semua cabang riwayat

Revision ID: d8a621e86559
Revises: 4d557a9e8bbf, bf57018ff681
Create Date: 2025-08-31 20:02:56.348104

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8a621e86559'
down_revision: Union[str, Sequence[str], None] = ('4d557a9e8bbf', 'bf57018ff681')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
