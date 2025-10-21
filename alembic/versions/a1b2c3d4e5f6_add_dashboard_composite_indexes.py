"""add_dashboard_composite_indexes

Revision ID: a1b2c3d4e5f6
Revises: b71150711a61
Create Date: 2025-10-04 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'b71150711a61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Dashboard Performance Indexes for Invoice Model
    op.create_index('idx_invoice_status_paid_date', 'invoices', ['status_invoice', 'paid_at', 'total_harga'], unique=False)
    op.create_index('idx_invoice_late_payment', 'invoices', ['paid_at', 'tgl_jatuh_tempo'], unique=False)
    op.create_index('idx_invoice_monthly_summary', 'invoices', ['status_invoice', 'tgl_invoice', 'total_harga'], unique=False)
    op.create_index('idx_invoice_brand_date', 'invoices', ['brand', 'tgl_invoice'], unique=False)
    op.create_index('idx_invoice_payment_date', 'invoices', ['paid_at', 'tgl_jatuh_tempo'], unique=False)

    # Dashboard Performance Indexes for Pelanggan Model
    op.create_index('idx_pelanggan_brand_count', 'pelanggan', ['id_brand', 'nama'], unique=False)
    op.create_index('idx_pelanggan_location_count', 'pelanggan', ['alamat', 'id'], unique=False)
    op.create_index('idx_pelanggan_installation_month', 'pelanggan', ['tgl_instalasi', 'id_brand'], unique=False)
    op.create_index('idx_pelanggan_brand_location', 'pelanggan', ['id_brand', 'alamat'], unique=False)
    op.create_index('idx_pelanggan_active_subscription', 'pelanggan', ['id', 'layanan'], unique=False)

    # Dashboard Performance Indexes for Langganan Model
    op.create_index('idx_langganan_status_count', 'langganan', ['status', 'pelanggan_id'], unique=False)
    op.create_index('idx_langganan_active_customer', 'langganan', ['status', 'paket_layanan_id'], unique=False)
    op.create_index('idx_langganan_due_analysis', 'langganan', ['tgl_jatuh_tempo', 'status', 'metode_pembayaran'], unique=False)
    op.create_index('idx_langganan_revenue_tracking', 'langganan', ['status', 'harga_awal', 'tgl_jatuh_tempo'], unique=False)
    op.create_index('idx_langganan_package_customer', 'langganan', ['paket_layanan_id', 'pelanggan_id', 'status'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop Dashboard Performance Indexes
    op.drop_index('idx_invoice_status_paid_date', table_name='invoices')
    op.drop_index('idx_invoice_late_payment', table_name='invoices')
    op.drop_index('idx_invoice_monthly_summary', table_name='invoices')
    op.drop_index('idx_invoice_brand_date', table_name='invoices')
    op.drop_index('idx_invoice_payment_date', table_name='invoices')

    op.drop_index('idx_pelanggan_brand_count', table_name='pelanggan')
    op.drop_index('idx_pelanggan_location_count', table_name='pelanggan')
    op.drop_index('idx_pelanggan_installation_month', table_name='pelanggan')
    op.drop_index('idx_pelanggan_brand_location', table_name='pelanggan')
    op.drop_index('idx_pelanggan_active_subscription', table_name='pelanggan')

    op.drop_index('idx_langganan_status_count', table_name='langganan')
    op.drop_index('idx_langganan_active_customer', table_name='langganan')
    op.drop_index('idx_langganan_due_analysis', table_name='langganan')
    op.drop_index('idx_langganan_revenue_tracking', table_name='langganan')
    op.drop_index('idx_langganan_package_customer', table_name='langganan')