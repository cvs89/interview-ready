"""Add interview sessions.

Revision ID: 20261002_0004
Revises: 20261002_0003
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261004_0004"
down_revision: str | None = "20261002_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Revision ID should follow naming convention 20261002_0004
revision = "20261002_0004"

session_status = postgresql.ENUM(
    "READY",
    "ACTIVE",
    "ENDED",
    name="session_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    session_status.create(bind, checkfirst=True)

    op.create_table(
        "interview_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("livekit_room_name", sa.String(length=128), nullable=False),
        sa.Column(
            "status",
            session_status,
            server_default=sa.text("'READY'::session_status"),
            nullable=False,
        ),
        sa.Column("candidate_joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("interviewer_joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_interview_sessions_booking",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interview_sessions"),
        sa.UniqueConstraint("booking_id", name="uq_interview_sessions_booking_id"),
        sa.UniqueConstraint("livekit_room_name", name="uq_interview_sessions_room_name"),
    )
    op.create_index(
        "ix_interview_sessions_booking_id",
        "interview_sessions",
        ["booking_id"],
    )
    op.create_index(
        "ix_interview_sessions_status",
        "interview_sessions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_interview_sessions_status", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_booking_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")
    session_status.drop(op.get_bind(), checkfirst=True)
