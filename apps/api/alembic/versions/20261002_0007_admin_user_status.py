"""Add user account status for admin controls.

Revision ID: 20261002_0007
Revises: 20261002_0006
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0007"
down_revision: str | None = "20261002_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    user_status = postgresql.ENUM("ACTIVE", "SUSPENDED", "DISABLED", name="user_status")
    user_status.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "SUSPENDED", "DISABLED", name="user_status"),
            server_default="ACTIVE",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_users_status",
        "users",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_users_status", table_name="users")
    op.drop_column("users", "status")

    user_status = postgresql.ENUM("ACTIVE", "SUSPENDED", "DISABLED", name="user_status")
    user_status.drop(op.get_bind(), checkfirst=True)
