import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, Index, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.identity import User


class InAppNotification(Base):
    __tablename__ = "in_app_notifications"
    __table_args__ = (
        Index("ix_in_app_notifications_user_unread", "user_id", "read_at"),
        Index("ix_in_app_notifications_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_in_app_notifications_user", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(foreign_keys=[user_id])


class NotificationDeliveryLog(Base):
    __tablename__ = "notification_delivery_logs"
    __table_args__ = (
        UniqueConstraint(
            "idempotency_key",
            name="uq_notification_delivery_logs_idempotency_key",
        ),
        Index(
            "ix_notification_delivery_recipient",
            "recipient_user_id",
            "event_type",
        ),
        Index("ix_notification_delivery_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "users.id",
            name="fk_notification_delivery_logs_recipient",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SENT", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    recipient: Mapped["User"] = relationship(foreign_keys=[recipient_user_id])
