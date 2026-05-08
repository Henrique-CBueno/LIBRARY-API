"""add reservation notifications

Revision ID: b71f3d9a6c20
Revises: 1200eae27439
Create Date: 2026-05-08 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b71f3d9a6c20"
down_revision: Union[str, Sequence[str], None] = "1200eae27439"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS "
        "'RESERVATION_CREATED'"
    )
    op.execute(
        "ALTER TYPE notificationtype ADD VALUE IF NOT EXISTS "
        "'RESERVATION_CANCELLED'"
    )
    op.add_column(
        "notifications",
        sa.Column("reservation_id", sa.String(), nullable=True),
    )
    op.create_foreign_key(
        "fk_notifications_reservation_id_reservations",
        "notifications",
        "reservations",
        ["reservation_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_notifications_reservation_id_reservations",
        "notifications",
        type_="foreignkey",
    )
    op.drop_column("notifications", "reservation_id")
