"""add fine paid at to loans

Revision ID: 9c4e0b71d2a8
Revises: 55022d3a2d13
Create Date: 2026-05-08 01:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9c4e0b71d2a8"
down_revision: Union[str, Sequence[str], None] = "55022d3a2d13"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "loans",
        sa.Column("fine_paid_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("loans", "fine_paid_at")
