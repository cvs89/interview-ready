import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.identity import User


class RubricStatus(StrEnum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    LOCKED = "LOCKED"


class InterviewRubric(TimestampMixin, Base):
    __tablename__ = "interview_rubrics"
    __table_args__ = (
        CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 1 AND technical_score <= 5)",
            name="ck_rubrics_technical_score_range",
        ),
        CheckConstraint(
            "problem_solving_score IS NULL OR "
            "(problem_solving_score >= 1 AND problem_solving_score <= 5)",
            name="ck_rubrics_problem_solving_score_range",
        ),
        CheckConstraint(
            "communication_score IS NULL OR "
            "(communication_score >= 1 AND communication_score <= 5)",
            name="ck_rubrics_communication_score_range",
        ),
        Index("ix_interview_rubrics_booking_id", "booking_id"),
        Index("ix_interview_rubrics_interviewer_id", "interviewer_id"),
        Index("ix_interview_rubrics_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", name="fk_rubrics_booking", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_rubrics_interviewer", ondelete="CASCADE"),
        nullable=False,
    )
    technical_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    problem_solving_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    communication_score: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    detailed_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    private_interviewer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[RubricStatus] = mapped_column(
        Enum(
            RubricStatus,
            name="rubric_status",
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        default=RubricStatus.DRAFT,
        server_default=RubricStatus.DRAFT.value,
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="rubric")
    interviewer: Mapped["User"] = relationship(foreign_keys=[interviewer_id])


class InterviewerReview(TimestampMixin, Base):
    __tablename__ = "interviewer_reviews"
    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="ck_reviews_rating_range",
        ),
        Index("ix_interviewer_reviews_interviewer_id", "interviewer_id"),
        Index("ix_interviewer_reviews_candidate_id", "candidate_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", name="fk_reviews_booking", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_reviews_candidate", ondelete="CASCADE"),
        nullable=False,
    )
    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_reviews_interviewer", ondelete="CASCADE"),
        nullable=False,
    )
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    review: Mapped[str | None] = mapped_column(Text, nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="review")
    candidate: Mapped["User"] = relationship(foreign_keys=[candidate_id])
    interviewer: Mapped["User"] = relationship(foreign_keys=[interviewer_id])
