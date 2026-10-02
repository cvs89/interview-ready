import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.rate_limit import RateLimiter
from app.db.session import get_session
from app.models.availability import AvailabilityStatus
from app.models.booking import BookingStatus
from app.models.identity import User, UserRole, UserStatus
from app.schemas.admin import (
    AdminBookingItemResponse,
    AdminBookingListResponse,
    AdminPaymentListResponse,
    AdminSlotListResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserStatusUpdateRequest,
    AdminVerificationListResponse,
)
from app.services.admin import AdminService

admin_router = APIRouter(prefix="/admin", tags=["admin"])

Session = Annotated[AsyncSession, Depends(get_session)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]


@admin_router.get(
    "/users",
    response_model=AdminUserListResponse,
    dependencies=[Depends(RateLimiter(action="search_users", limit=60, window_seconds=60))],
)
async def list_users(
    _: AdminUser,
    session: Session,
    search: str | None = None,
    role: UserRole | None = None,
    status: UserStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListResponse:
    return await AdminService(session).list_users(
        search=search,
        role=role,
        status=status,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: uuid.UUID,
    _: AdminUser,
    session: Session,
) -> AdminUserResponse:
    return await AdminService(session).get_user(user_id)


@admin_router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def update_user_status(
    user_id: uuid.UUID,
    request: AdminUserStatusUpdateRequest,
    admin: AdminUser,
    session: Session,
) -> AdminUserResponse:
    return await AdminService(session).update_user_status(user_id, admin, request)


@admin_router.get("/verifications", response_model=AdminVerificationListResponse)
async def list_verifications(
    _: AdminUser,
    session: Session,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminVerificationListResponse:
    return await AdminService(session).list_verifications(
        status=status,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/bookings", response_model=AdminBookingListResponse)
async def list_bookings(
    _: AdminUser,
    session: Session,
    status: BookingStatus | None = None,
    candidate_id: uuid.UUID | None = None,
    interviewer_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminBookingListResponse:
    return await AdminService(session).list_bookings(
        status=status,
        candidate_id=candidate_id,
        interviewer_id=interviewer_id,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/bookings/{booking_id}", response_model=AdminBookingItemResponse)
async def get_booking(
    booking_id: uuid.UUID,
    _: AdminUser,
    session: Session,
) -> AdminBookingItemResponse:
    return await AdminService(session).get_booking_detail(booking_id)


@admin_router.get("/payments", response_model=AdminPaymentListResponse)
async def list_payments(
    _: AdminUser,
    session: Session,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminPaymentListResponse:
    return await AdminService(session).list_payments(
        status=status,
        limit=limit,
        offset=offset,
    )


@admin_router.get("/slots", response_model=AdminSlotListResponse)
async def list_slots(
    _: AdminUser,
    session: Session,
    interviewer_id: uuid.UUID | None = None,
    status: AvailabilityStatus | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminSlotListResponse:
    return await AdminService(session).list_slots(
        interviewer_id=interviewer_id,
        status=status,
        limit=limit,
        offset=offset,
    )
