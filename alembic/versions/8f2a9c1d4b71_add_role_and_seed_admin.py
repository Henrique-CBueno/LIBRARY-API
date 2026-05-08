"""add role to users and seed admin

Revision ID: 8f2a9c1d4b71
Revises: b71f3d9a6c20
Create Date: 2026-05-08 00:00:00.000000

"""

from datetime import datetime
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import uuid6 as uuid

from app.config.security.hashing import hash_password


# revision identifiers, used by Alembic.
revision: str = "8f2a9c1d4b71"
down_revision: Union[str, Sequence[str], None] = "b71f3d9a6c20"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_admin_seed_values():
    email = os.environ.get("INITIAL_ADMIN_EMAIL")
    name = os.environ.get("INITIAL_ADMIN_NAME")
    password = os.environ.get("INITIAL_ADMIN_PASSWORD")

    if not email or not name or not password:
        return None

    return email, name, password


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            server_default="USER",
        ),
    )

    admin_seed_values = _get_admin_seed_values()

    if not admin_seed_values:
        return

    email, name, password = admin_seed_values
    bind = op.get_bind()

    existing = bind.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": email},
    ).fetchone()

    if existing:
        bind.execute(
            sa.text(
                "UPDATE users SET role = :role, is_active = TRUE WHERE email = :email"
            ),
            {"role": "ADMIN", "email": email},
        )
        return

    bind.execute(
        sa.text(
            """
            INSERT INTO users (id, name, email, password, created_at, is_active, role)
            VALUES (:id, :name, :email, :password, :created_at, :is_active, :role)
            """
        ),
        {
            "id": str(uuid.uuid6()),
            "name": name,
            "email": email,
            "password": hash_password(password),
            "created_at": datetime.utcnow(),
            "is_active": True,
            "role": "ADMIN",
        },
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "role")
