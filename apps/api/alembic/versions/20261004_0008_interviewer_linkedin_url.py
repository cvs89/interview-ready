"""Add linkedin_url to interviewer_profiles.

Revision ID: 20261004_0008
Revises: 20261002_0007
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261004_0008"
down_revision: str | None = "20261002_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interviewer_profiles",
        sa.Column("linkedin_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interviewer_profiles", "linkedin_url")
