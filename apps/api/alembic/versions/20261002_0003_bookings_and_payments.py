"""Add bookings, payments, and payment webhook events.

Revision ID: 20261002_0003
Revises: 20261002_0002
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0003"
down_revision: str | None = "20261002_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

booking_status = postgresql.ENUM(
    "PENDING_PAYMENT",
    "CONFIRMED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
    "EXPIRED",
    "NO_SHOW",
    "REFUNDED",
    name="booking_status",
    create_type=False,
)
payment_status = postgresql.ENUM(
    "PENDING",
    "REQUIRES_ACTION",
    "PAID",
    "FAILED",
    "REFUNDED",
    "PARTIALLY_REFUNDED",
    "CANCELLED",
    name="payment_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    booking_status.create(bind, checkfirst=True)
    payment_status.create(bind, checkfirst=True)

    op.create_table(
        "bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("interviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            booking_status,
            server_default=sa.text("'PENDING_PAYMENT'::booking_status"),
            nullable=False,
        ),
        sa.Column("price_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("price_minor >= 0", name="ck_bookings_price_nonnegative"),
        sa.CheckConstraint("currency = upper(currency)", name="ck_bookings_currency_uppercase"),
        sa.ForeignKeyConstraint(
            ["slot_id"],
            ["availability_slots.id"],
            name="fk_bookings_slot",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
            name="fk_bookings_candidate",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["interviewer_id"],
            ["users.id"],
            name="fk_bookings_interviewer",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_bookings"),
        sa.UniqueConstraint("slot_id", name="uq_bookings_slot_id"),
    )
    op.create_index(
        "ix_bookings_candidate_status",
        "bookings",
        ["candidate_id", "status"],
    )
    op.create_index(
        "ix_bookings_interviewer_status",
        "bookings",
        ["interviewer_id", "status"],
    )
    op.create_index(
        "ix_bookings_status_created",
        "bookings",
        ["status", "created_at"],
    )

    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_payment_id", sa.String(length=255), nullable=True),
        sa.Column("provider_checkout_session_id", sa.String(length=255), nullable=True),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.CHAR(length=3), nullable=False),
        sa.Column(
            "status",
            payment_status,
            server_default=sa.text("'PENDING'::payment_status"),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("amount_minor >= 0", name="ck_payments_amount_nonnegative"),
        sa.CheckConstraint("currency = upper(currency)", name="ck_payments_currency_uppercase"),
        sa.ForeignKeyConstraint(
            ["booking_id"],
            ["bookings.id"],
            name="fk_payments_booking",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["candidate_id"],
            ["users.id"],
            name="fk_payments_candidate",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payments"),
        sa.UniqueConstraint("booking_id", name="uq_payments_booking_id"),
        sa.UniqueConstraint("provider_payment_id", name="uq_payments_provider_payment_id"),
        sa.UniqueConstraint(
            "provider_checkout_session_id", name="uq_payments_provider_checkout_session_id"
        ),
    )
    op.create_index(
        "ix_payments_booking_status",
        "payments",
        ["booking_id", "status"],
    )
    op.create_index(
        "ix_payments_candidate_status",
        "payments",
        ["candidate_id", "status"],
    )

    op.create_table(
        "payment_webhook_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("provider_event_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_payment_webhook_events"),
        sa.UniqueConstraint(
            "provider_event_id", name="uq_payment_webhook_events_provider_event_id"
        ),
    )
    op.create_index(
        "ix_webhook_events_provider_type",
        "payment_webhook_events",
        ["provider", "event_type"],
    )
    op.create_index(
        "ix_webhook_events_processed_at",
        "payment_webhook_events",
        ["processed_at"],
    )


def downgrade() -> None:
    op.drop_table("payment_webhook_events")
    op.drop_table("payments")
    op.drop_table("bookings")
    payment_status.drop(op.get_bind(), checkfirst=True)
    booking_status.drop(op.get_bind(), checkfirst=True)
