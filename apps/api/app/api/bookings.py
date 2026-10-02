import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.session import get_session
from app.models.identity import User
from app.schemas.bookings import (
    BookingReserveRequest,
    BookingResponse,
    PaymentCheckoutRequest,
    PaymentCheckoutResponse,
    WebhookEventResponse,
)
from app.schemas.sessions import JoinStatusResponse
from app.services.bookings import BookingService, PaymentService
from app.services.sessions import DesktopAuthService

bookings_router = APIRouter(prefix="/bookings", tags=["bookings"])
payments_router = APIRouter(prefix="/payments", tags=["payments"])
webhooks_router = APIRouter(prefix="/webhooks/payments", tags=["webhooks"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@bookings_router.post(
    "/reserve",
    response_model=BookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RateLimiter(action="reserve_slot", limit=10, window_seconds=60))],
)
async def reserve_slot(
    request: BookingReserveRequest,
    user: CurrentUser,
    session: Session,
    raw_request: Request,
) -> BookingResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    return await BookingService(session, settings=settings).reserve_slot(user, request)


@bookings_router.get("/me", response_model=list[BookingResponse])
async def list_own_bookings(
    user: CurrentUser,
    session: Session,
    raw_request: Request,
) -> list[BookingResponse]:
    settings = getattr(raw_request.app.state, "settings", None)
    return await BookingService(session, settings=settings).list_user_bookings(user)


@bookings_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
    raw_request: Request,
) -> BookingResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    return await BookingService(session, settings=settings).get_booking(user, booking_id)


@bookings_router.get("/{booking_id}/join-status", response_model=JoinStatusResponse)
async def get_join_status(
    booking_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
    raw_request: Request,
) -> JoinStatusResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    return await DesktopAuthService(session, settings=settings).get_join_status(user, booking_id)


@payments_router.post(
    "/{booking_id}/checkout",
    response_model=PaymentCheckoutResponse,
    dependencies=[Depends(RateLimiter(action="checkout_payment", limit=10, window_seconds=60))],
)
async def create_checkout(
    booking_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
    raw_request: Request,
    request: PaymentCheckoutRequest | None = None,
) -> PaymentCheckoutResponse:
    settings = getattr(raw_request.app.state, "settings", None)
    req = request or PaymentCheckoutRequest()
    return await PaymentService(session, settings=settings).create_checkout(user, booking_id, req)


@webhooks_router.post("/{provider}", response_model=WebhookEventResponse)
async def handle_payment_webhook(
    provider: str,
    raw_request: Request,
    session: Session,
) -> WebhookEventResponse:
    body = await raw_request.body()
    headers = dict(raw_request.headers)
    settings = getattr(raw_request.app.state, "settings", None)
    return await PaymentService(session, settings=settings).process_webhook(
        provider_name=provider,
        payload_bytes=body,
        headers=headers,
    )
