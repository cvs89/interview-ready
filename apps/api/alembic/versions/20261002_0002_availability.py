"""Add interviewer verification and availability.

Revision ID: 20261002_0002
Revises: 20261002_0001
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0002"
down_revision: str | None = "20261002_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

verification_status = postgresql.ENUM(
    "PENDING",
    "IN_REVIEW",
    "APPROVED",
    "REJECTED",
    name="verification_status",
    create_type=False,
)
availability_status = postgresql.ENUM(
    "AVAILABLE",
    "RESERVED",
    "BOOKED",
    "BLOCKED",
    name="availability_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
    verification_status.create(bind, checkfirst=True)
    availability_status.create(bind, checkfirst=True)

    op.create_check_constraint(
        "ck_interviewer_profiles_default_price_pair",
        "interviewer_profiles",
        "(default_rate_minor IS NULL AND currency IS NULL) OR "
        "(default_rate_minor IS NOT NULL AND currency IS NOT NULL)",
    )

    op.create_table(
        "interviewer_verifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            verification_status,
            server_default=sa.text("'PENDING'::verification_status"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["interviewer_profiles.id"],
            name="fk_verifications_profile",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewed_by"],
            ["users.id"],
            name="fk_verifications_reviewer",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_interviewer_verifications"),
        sa.UniqueConstraint("interviewer_id", name="uq_interviewer_verifications_interviewer_id"),
    )
    op.create_index("ix_interviewer_verifications_status", "interviewer_verifications", ["status"])

    op.create_table(
        "availability_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column(
            "status",
            availability_status,
            server_default=sa.text("'AVAILABLE'::availability_status"),
            nullable=False,
        ),
        sa.Column("reserved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("reservation_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("end_time > start_time", name="ck_availability_slots_time_range"),
        sa.CheckConstraint("price_minor >= 0", name="ck_availability_slots_price_nonnegative"),
        sa.CheckConstraint(
            "currency = upper(currency)", name="ck_availability_slots_currency_uppercase"
        ),
        sa.CheckConstraint(
            "status != 'RESERVED' OR "
            "(reserved_by IS NOT NULL AND reservation_expires_at IS NOT NULL)",
            name="ck_availability_slots_reservation_metadata",
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["interviewer_profiles.id"],
            name="fk_slots_interviewer",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reserved_by"],
            ["users.id"],
            name="fk_slots_reserved_by",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_availability_slots"),
    )
    op.create_index(
        "ix_availability_slots_interviewer_start",
        "availability_slots",
        ["interviewer_id", "start_time"],
    )
    op.create_index(
        "ix_availability_slots_status_start",
        "availability_slots",
        ["status", "start_time"],
    )
    op.execute(
        "ALTER TABLE availability_slots ADD CONSTRAINT "
        "ex_availability_slots_no_overlap EXCLUDE USING gist "
        "(interviewer_id WITH =, tstzrange(start_time, end_time, '[)') WITH &&)"
    )


def downgrade() -> None:
    op.drop_table("availability_slots")
    op.drop_index("ix_interviewer_verifications_status", table_name="interviewer_verifications")
    op.drop_table("interviewer_verifications")
    op.drop_constraint(
        "ck_interviewer_profiles_default_price_pair",
        "interviewer_profiles",
        type_="check",
    )
    availability_status.drop(op.get_bind(), checkfirst=True)
    verification_status.drop(op.get_bind(), checkfirst=True)
