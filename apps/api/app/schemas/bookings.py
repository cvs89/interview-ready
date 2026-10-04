import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.models.booking import BookingStatus, PaymentStatus

Currency = Annotated[str, Field(min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")]


class BookingReserveRequest(BaseModel):
    slot_id: uuid.UUID


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slot_id: uuid.UUID
    candidate_id: uuid.UUID
    interviewer_id: uuid.UUID
    status: BookingStatus
    price_minor: int
    currency: str
    reservation_expires_at: datetime | None = None
    created_at: datetime
    confirmed_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None


class PaymentCheckoutRequest(BaseModel):
    success_url: str | None = None
    cancel_url: str | None = None
    provider: str | None = None


class PaymentCheckoutResponse(BaseModel):
    booking_id: uuid.UUID
    payment_id: uuid.UUID
    provider: str
    amount_minor: int
    currency: str
    status: PaymentStatus
    checkout_url: str
    provider_checkout_session_id: str | None = None
    expires_at: datetime | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    candidate_id: uuid.UUID
    provider: str
    provider_payment_id: str | None = None
    provider_checkout_session_id: str | None = None
    amount_minor: int
    currency: str
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None = None
    refunded_at: datetime | None = None


class WebhookEventResponse(BaseModel):
    received: bool = True
    status: str
