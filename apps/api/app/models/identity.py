import uuid
from datetime import datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CHAR,
    BigInteger,
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    false,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.db.types import UTCDateTime

if TYPE_CHECKING:
    from app.models.availability import AvailabilitySlot, InterviewerVerification


class UserRole(StrEnum):
    CANDIDATE = "CANDIDATE"
    INTERVIEWER = "INTERVIEWER"
    ADMIN = "ADMIN"


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="ck_users_email_normalized"),
        CheckConstraint("length(trim(full_name)) > 0", name="ck_users_full_name_nonempty"),
        Index("ix_users_role", "role"),
        Index("ix_users_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.CANDIDATE,
        server_default=UserRole.CANDIDATE.value,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"),
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
        nullable=False,
    )
    email_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )
    auth_provider: Mapped[str | None] = mapped_column(String(100))
    last_login_at: Mapped[datetime | None] = mapped_column(UTCDateTime())

    interviewer_profile: Mapped["InterviewerProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )


class InterviewerProfile(TimestampMixin, Base):
    __tablename__ = "interviewer_profiles"
    __table_args__ = (
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_interviewer_profiles_years_nonnegative",
        ),
        CheckConstraint(
            "default_rate_minor IS NULL OR default_rate_minor >= 0",
            name="ck_interviewer_profiles_rate_nonnegative",
        ),
        CheckConstraint(
            "currency IS NULL OR currency = upper(currency)",
            name="ck_interviewer_profiles_currency_uppercase",
        ),
        CheckConstraint(
            "(default_rate_minor IS NULL AND currency IS NULL) OR "
            "(default_rate_minor IS NOT NULL AND currency IS NOT NULL)",
            name="ck_interviewer_profiles_default_price_pair",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    bio: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(String(200))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    default_rate_minor: Mapped[int | None] = mapped_column(BigInteger)
    currency: Mapped[str | None] = mapped_column(CHAR(3))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="interviewer_profile")
    skill_links: Mapped[list["InterviewerSkill"]] = relationship(
        back_populates="interviewer", cascade="all, delete-orphan"
    )
    verification: Mapped["InterviewerVerification | None"] = relationship(
        back_populates="interviewer", cascade="all, delete-orphan", uselist=False
    )
    availability_slots: Mapped[list["AvailabilitySlot"]] = relationship(
        back_populates="interviewer", cascade="all, delete-orphan"
    )


class Skill(Base):
    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint("length(trim(name)) > 0", name="ck_skills_name_nonempty"),
        CheckConstraint("length(trim(slug)) > 0", name="ck_skills_slug_nonempty"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)

    interviewer_links: Mapped[list["InterviewerSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class InterviewerSkill(Base):
    __tablename__ = "interviewer_skills"
    __table_args__ = (
        UniqueConstraint("interviewer_id", "skill_id", name="uq_interviewer_skills_pair"),
        CheckConstraint(
            "years_experience IS NULL OR years_experience >= 0",
            name="ck_interviewer_skills_years_nonnegative",
        ),
        Index("ix_interviewer_skills_skill_id", "skill_id"),
    )

    interviewer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("interviewer_profiles.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    years_experience: Mapped[int | None] = mapped_column(Integer)

    interviewer: Mapped[InterviewerProfile] = relationship(back_populates="skill_links")
    skill: Mapped[Skill] = relationship(back_populates="interviewer_links")
