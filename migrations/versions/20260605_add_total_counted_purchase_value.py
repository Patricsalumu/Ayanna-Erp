"""Add total_counted_purchase_value to stock_inventaire and populate it

Revision ID: 20260605_add_total_counted_purchase_value
Revises: 
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260605_add_total_counted_purchase_value'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add column (if it doesn't exist already)
    try:
        op.add_column('stock_inventaire', sa.Column('total_counted_purchase_value', sa.Numeric(15, 2), nullable=True, server_default='0.0'))
    except Exception:
        # Column may already exist; ignore
        pass

    # Populate the column from stock_inventaire_item
    conn = op.get_bind()
    conn.execute(sa.text(
        """
        UPDATE stock_inventaire SET total_counted_purchase_value = (
            SELECT COALESCE(SUM(COALESCE(counted_stock,0) * COALESCE(unit_cost,0)),0)
            FROM stock_inventaire_item
            WHERE inventory_id = stock_inventaire.id
        )
        """
    ))


def downgrade():
    try:
        op.drop_column('stock_inventaire', 'total_counted_purchase_value')
    except Exception:
        pass
