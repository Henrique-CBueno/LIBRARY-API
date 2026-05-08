"""add fine paid amount to loans

Revision ID: 4a1d6c72b9e0
Revises: 9c4e0b71d2a8
Create Date: 2026-05-08 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4a1d6c72b9e0"
down_revision: Union[str, Sequence[str], None] = "9c4e0b71d2a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "loans",
        sa.Column(
            "fine_paid_amount",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0",
        ),
    )
    op.alter_column(
        "loans",
        "fine_paid_amount",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("loans", "fine_paid_amount")
