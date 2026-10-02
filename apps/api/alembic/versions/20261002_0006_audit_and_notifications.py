"""Add audit logs and notifications.

Revision ID: 20261002_0006
Revises: 20261002_0005
Create Date: 2026-10-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20261002_0006"
down_revision: str | None = "20261002_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Table audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("request_id", sa.String(length=255), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id"],
            ["users.id"],
            name="fk_audit_logs_actor",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_logs"),
    )
    op.create_index(
        "ix_audit_logs_actor_user_id",
        "audit_logs",
        ["actor_user_id"],
    )
    op.create_index(
        "ix_audit_logs_event_type",
        "audit_logs",
        ["event_type"],
    )
    op.create_index(
        "ix_audit_logs_resource",
        "audit_logs",
        ["resource_type", "resource_id"],
    )
    op.create_index(
        "ix_audit_logs_created_at",
        "audit_logs",
        ["created_at"],
    )

    # 2. Table in_app_notifications
    op.create_table(
        "in_app_notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "data",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_in_app_notifications_user",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_in_app_notifications"),
    )
    op.create_index(
        "ix_in_app_notifications_user_unread",
        "in_app_notifications",
        ["user_id", "read_at"],
    )
    op.create_index(
        "ix_in_app_notifications_created_at",
        "in_app_notifications",
        ["created_at"],
    )

    # 3. Table notification_delivery_logs
    op.create_table(
        "notification_delivery_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("channel", sa.String(length=50), nullable=False),
        sa.Column("reference_id", sa.String(length=255), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"],
            ["users.id"],
            name="fk_notification_delivery_logs_recipient",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_notification_delivery_logs"),
        sa.UniqueConstraint(
            "idempotency_key", name="uq_notification_delivery_logs_idempotency_key"
        ),
    )
    op.create_index(
        "ix_notification_delivery_recipient",
        "notification_delivery_logs",
        ["recipient_user_id", "event_type"],
    )
    op.create_index(
        "ix_notification_delivery_created_at",
        "notification_delivery_logs",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_delivery_created_at", table_name="notification_delivery_logs")
    op.drop_index("ix_notification_delivery_recipient", table_name="notification_delivery_logs")
    op.drop_table("notification_delivery_logs")

    op.drop_index("ix_in_app_notifications_created_at", table_name="in_app_notifications")
    op.drop_index("ix_in_app_notifications_user_unread", table_name="in_app_notifications")
    op.drop_table("in_app_notifications")

    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_event_type", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
