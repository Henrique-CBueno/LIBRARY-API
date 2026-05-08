"""add is_active to authors and books

Revision ID: 1b8d0f4a9c32
Revises: 85b770cc6eed
Create Date: 2026-05-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b8d0f4a9c32"
down_revision: Union[str, Sequence[str], None] = "85b770cc6eed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "authors",
        sa.Column("is_active", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "books",
        sa.Column("is_active", sa.Boolean(), nullable=True),
    )

    op.execute("UPDATE authors SET is_active = TRUE")
    op.execute("UPDATE books SET is_active = TRUE")

    op.alter_column("authors", "is_active", nullable=False)
    op.alter_column("books", "is_active", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("books", "is_active")
    op.drop_column("authors", "is_active")
