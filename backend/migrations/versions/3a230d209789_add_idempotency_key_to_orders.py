"""add idempotency_key to orders

Revision ID: 3a230d209789
Revises: 007b5d93015a
Create Date: 2026-06-16 22:43:25.141997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a230d209789'
down_revision: Union[str, Sequence[str], None] = '007b5d93015a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Client-supplied per-attempt token for idempotent checkout (ADR-0013). Nullable +
    # unique: existing rows get NULL, and NULLs stay distinct in Postgres.
    op.add_column("orders", sa.Column("idempotency_key", sa.String(), nullable=True))
    op.create_index(
        op.f("ix_orders_idempotency_key"), "orders", ["idempotency_key"], unique=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_orders_idempotency_key"), table_name="orders")
    op.drop_column("orders", "idempotency_key")
