import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CHAR,
    JSON,
    BigInteger,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.availability import AvailabilitySlot
    from app.models.feedback import InterviewerReview, InterviewRubric
    from app.models.identity import User
    from app.models.session import InterviewSession


class BookingStatus(StrEnum):
    PENDING_PAYMENT = "PENDING_PAYMENT"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    NO_SHOW = "NO_SHOW"
    REFUNDED = "REFUNDED"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    PAID = "PAID"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    CANCELLED = "CANCELLED"


class Booking(TimestampMixin, Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("price_minor >= 0", name="ck_bookings_price_nonnegative"),
        CheckConstraint("currency = upper(currency)", name="ck_bookings_currency_uppercase"),
        UniqueConstraint("slot_id", name="uq_bookings_slot_id"),
        Index("ix_bookings_candidate_status", "candidate_id", "status"),
        Index("ix_bookings_interviewer_status", "interviewer_id", "status"),
        Index("ix_bookings_status_created", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slot_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("availability_slots.id", name="fk_bookings_slot", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_bookings_candidate", ondelete="CASCADE"),
        nullable=False,
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_bookings_interviewer", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[BookingStatus] = mapped_column(
        Enum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING_PAYMENT,
        server_default=BookingStatus.PENDING_PAYMENT.value,
        nullable=False,
    )
    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    completed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    cancelled_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    slot: Mapped["AvailabilitySlot"] = relationship(back_populates="booking")
    candidate: Mapped["User"] = relationship(foreign_keys=[candidate_id])
    interviewer: Mapped["User"] = relationship(foreign_keys=[interviewer_id])
    payment: Mapped["Payment | None"] = relationship(
        back_populates="booking", cascade="all, delete-orphan", uselist=False
    )
    interview_session: Mapped["InterviewSession | None"] = relationship(
        back_populates="booking", cascade="all, delete-orphan", uselist=False
    )
    rubric: Mapped["InterviewRubric | None"] = relationship(
        back_populates="booking", cascade="all, delete-orphan", uselist=False
    )
    review: Mapped["InterviewerReview | None"] = relationship(
        back_populates="booking", cascade="all, delete-orphan", uselist=False
    )


class Payment(TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_minor >= 0", name="ck_payments_amount_nonnegative"),
        CheckConstraint("currency = upper(currency)", name="ck_payments_currency_uppercase"),
        UniqueConstraint("booking_id", name="uq_payments_booking_id"),
        Index("ix_payments_booking_status", "booking_id", "status"),
        Index("ix_payments_candidate_status", "candidate_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", name="fk_payments_booking", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_payments_candidate", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    provider_checkout_session_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
        nullable=False,
    )
    paid_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    refunded_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    booking: Mapped[Booking] = relationship(back_populates="payment")
    candidate: Mapped["User"] = relationship(foreign_keys=[candidate_id])


class PaymentWebhookEvent(Base):
    __tablename__ = "payment_webhook_events"
    __table_args__ = (
        UniqueConstraint("provider_event_id", name="uq_payment_webhook_events_provider_event_id"),
        Index("ix_webhook_events_provider_type", "provider", "event_type"),
        Index("ix_webhook_events_processed_at", "processed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime(),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
