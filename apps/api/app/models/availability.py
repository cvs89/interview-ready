import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.identity import InterviewerProfile, User


class VerificationStatus(StrEnum):
    PENDING = "PENDING"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class AvailabilityStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    RESERVED = "RESERVED"
    BOOKED = "BOOKED"
    BLOCKED = "BLOCKED"


class InterviewerVerification(Base):
    __tablename__ = "interviewer_verifications"
    __table_args__ = (
        UniqueConstraint("interviewer_id", name="uq_interviewer_verifications_interviewer_id"),
        Index("ix_interviewer_verifications_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviewer_profiles.id", name="fk_verifications_profile", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        server_default=VerificationStatus.PENDING.value,
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_verifications_reviewer", ondelete="SET NULL")
    )
    notes: Mapped[str | None] = mapped_column(Text)

    interviewer: Mapped["InterviewerProfile"] = relationship(back_populates="verification")
    reviewer: Mapped["User | None"] = relationship(foreign_keys=[reviewed_by])


class AvailabilitySlot(TimestampMixin, Base):
    __tablename__ = "availability_slots"
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="ck_availability_slots_time_range"),
        CheckConstraint("price_minor >= 0", name="ck_availability_slots_price_nonnegative"),
        CheckConstraint(
            "currency = upper(currency)", name="ck_availability_slots_currency_uppercase"
        ),
        CheckConstraint(
            "status != 'RESERVED' OR "
            "(reserved_by IS NOT NULL AND reservation_expires_at IS NOT NULL)",
            name="ck_availability_slots_reservation_metadata",
        ),
        Index("ix_availability_slots_interviewer_start", "interviewer_id", "start_time"),
        Index("ix_availability_slots_status_start", "status", "start_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviewer_profiles.id", name="fk_slots_interviewer", ondelete="CASCADE"),
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    end_time: Mapped[datetime] = mapped_column(UTCDateTime(), nullable=False)
    price_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(CHAR(3), nullable=False)
    status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, name="availability_status"),
        default=AvailabilityStatus.AVAILABLE,
        server_default=AvailabilityStatus.AVAILABLE.value,
        nullable=False,
    )
    reserved_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", name="fk_slots_reserved_by", ondelete="SET NULL")
    )
    reservation_expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    interviewer: Mapped["InterviewerProfile"] = relationship(back_populates="availability_slots")
    reserving_user: Mapped["User | None"] = relationship(foreign_keys=[reserved_by])
    booking: Mapped["Booking | None"] = relationship(back_populates="slot", uselist=False)
