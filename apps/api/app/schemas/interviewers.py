import uuid
from datetime import UTC, datetime
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.availability import (
    AvailabilityStatus,
    VerificationStatus,
)

Currency = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]


class ProfileUpsertRequest(BaseModel):
    bio: Annotated[str | None, Field(max_length=5000)] = None
    title: Annotated[str | None, Field(max_length=200)] = None
    years_experience: Annotated[int | None, Field(ge=0, le=80)] = None
    default_rate_minor: Annotated[int | None, Field(ge=0)] = None
    currency: Currency | None = None

    @model_validator(mode="after")
    def validate_default_price_pair(self) -> Self:
        price_set = "default_rate_minor" in self.model_fields_set
        currency_set = "currency" in self.model_fields_set
        if price_set != currency_set:
            raise ValueError("default_rate_minor and currency must be provided together")
        if price_set and (self.default_rate_minor is None) != (self.currency is None):
            raise ValueError("default_rate_minor and currency must both be set or both be null")
        return self


class SkillCreateRequest(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=100)]
    slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=120)]


class SkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str


class InterviewerSkillRequest(BaseModel):
    skill_id: uuid.UUID
    years_experience: Annotated[int | None, Field(ge=0, le=80)] = None


class InterviewerSkillResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    years_experience: int | None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    bio: str | None
    title: str | None
    years_experience: int | None
    default_rate_minor: int | None
    currency: str | None
    is_verified: bool
    verification_status: VerificationStatus
    skills: list[InterviewerSkillResponse]


class AvailabilitySlotCreateRequest(BaseModel):
    start_time: AwareDatetime
    end_time: AwareDatetime
    price_minor: Annotated[int | None, Field(ge=0)] = None
    currency: Currency | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_slot(self) -> Self:
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        if (self.price_minor is None) != (self.currency is None):
            raise ValueError("price_minor and currency must be provided together")
        return self


class AvailabilitySlotUpdateRequest(BaseModel):
    start_time: AwareDatetime | None = None
    end_time: AwareDatetime | None = None
    price_minor: Annotated[int | None, Field(ge=0)] = None
    currency: Currency | None = None

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_utc(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value else None

    @model_validator(mode="after")
    def validate_price_pair(self) -> Self:
        price_set = "price_minor" in self.model_fields_set
        currency_set = "currency" in self.model_fields_set
        if price_set != currency_set or (
            price_set and (self.price_minor is None or self.currency is None)
        ):
            raise ValueError("price_minor and currency must be provided together")
        return self


class AvailabilitySlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interviewer_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    price_minor: int
    currency: str
    status: AvailabilityStatus


class VerificationReviewRequest(BaseModel):
    status: Literal[VerificationStatus.APPROVED, VerificationStatus.REJECTED]
    notes: Annotated[str | None, Field(max_length=5000)] = None


class VerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interviewer_id: uuid.UUID
    status: VerificationStatus
    submitted_at: datetime
    reviewed_at: datetime | None
    reviewed_by: uuid.UUID | None
    notes: str | None
