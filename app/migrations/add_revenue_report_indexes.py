"""add indexes for revenue report performance

Revision ID: add_revenue_report_indexes
Revises: previous_migration
Create Date: 2024-01-01

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_revenue_report_indexes'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Index untuk invoice table yang sering diquery di revenue report
    op.create_index(
        'idx_invoice_status_paid_at',
        'invoice',
        ['status_invoice', 'paid_at']
    )

    op.create_index(
        'idx_invoice_paid_at_desc',
        'invoice',
        [sa.text('paid_at DESC')]
    )

    # Index untuk pelanggan alamat filtering
    op.create_index(
        'idx_pelanggan_alamat',
        'pelanggan',
        ['alamat']
    )

    # Index untuk pelanggan brand filtering
    op.create_index(
        'idx_pelanggan_id_brand',
        'pelanggan',
        ['id_brand']
    )

    # Composite index untuk join performance
    op.create_index(
        'idx_invoice_pelanggan_join',
        'invoice',
        ['pelanggan_id', 'status_invoice', 'paid_at']
    )

def downgrade():
    op.drop_index('idx_invoice_status_paid_at', table_name='invoice')
    op.drop_index('idx_invoice_paid_at_desc', table_name='invoice')
    op.drop_index('idx_pelanggan_alamat', table_name='pelanggan')
    op.drop_index('idx_pelanggan_id_brand', table_name='pelanggan')
    op.drop_index('idx_invoice_pelanggan_join', table_name='invoice')