import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.identity import UserRole, UserStatus


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    email_verified: bool
    auth_provider: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    items: list[AdminUserResponse]
    total: int
    limit: int
    offset: int


class AdminUserStatusUpdateRequest(BaseModel):
    status: UserStatus
    reason: str | None = Field(default=None, max_length=500)


class AdminInterviewerVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interviewer_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str
    title: str | None = None
    years_experience: int | None = None
    linkedin_url: str | None = None
    status: str
    submitted_at: datetime | None = None
    reviewed_at: datetime | None = None
    reviewed_by: uuid.UUID | None = None
    notes: str | None = None


class AdminVerificationListResponse(BaseModel):
    items: list[AdminInterviewerVerificationResponse]
    total: int
    limit: int
    offset: int


class AdminBookingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slot_id: uuid.UUID
    candidate_id: uuid.UUID
    candidate_name: str
    candidate_email: str
    interviewer_id: uuid.UUID
    interviewer_name: str
    interviewer_email: str
    status: str
    cancellation_reason: str | None = None
    slot_start_time: datetime
    slot_end_time: datetime
    price_minor: int
    currency: str
    payment_status: str | None = None
    created_at: datetime


class AdminBookingListResponse(BaseModel):
    items: list[AdminBookingItemResponse]
    total: int
    limit: int
    offset: int


class AdminPaymentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    amount_minor: int
    currency: str
    provider: str
    status: str
    provider_payment_id: str
    created_at: datetime
    updated_at: datetime


class AdminPaymentListResponse(BaseModel):
    items: list[AdminPaymentItemResponse]
    total: int
    limit: int
    offset: int


class AdminSlotItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    interviewer_id: uuid.UUID
    interviewer_name: str
    start_time: datetime
    end_time: datetime
    price_minor: int
    currency: str
    status: str
    created_at: datetime


class AdminSlotListResponse(BaseModel):
    items: list[AdminSlotItemResponse]
    total: int
    limit: int
    offset: int
