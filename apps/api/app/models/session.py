import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.booking import Booking


class SessionStatus(StrEnum):
    READY = "READY"
    ACTIVE = "ACTIVE"
    ENDED = "ENDED"


class InterviewSession(TimestampMixin, Base):
    __tablename__ = "interview_sessions"
    __table_args__ = (
        UniqueConstraint("booking_id", name="uq_interview_sessions_booking_id"),
        UniqueConstraint("livekit_room_name", name="uq_interview_sessions_room_name"),
        Index("ix_interview_sessions_booking_id", "booking_id"),
        Index("ix_interview_sessions_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", name="fk_interview_sessions_booking", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    livekit_room_name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus, name="session_status"),
        default=SessionStatus.READY,
        server_default=SessionStatus.READY.value,
        nullable=False,
    )
    candidate_joined_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    interviewer_joined_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    booking: Mapped["Booking"] = relationship(back_populates="interview_session")
