import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.availability import AvailabilityStatus
from app.models.booking import BookingStatus
from app.models.identity import User, UserRole, UserStatus
from app.repositories.bookings import BookingRepository
from app.repositories.interviewers import InterviewerRepository
from app.repositories.users import UserRepository
from app.schemas.admin import (
    AdminBookingItemResponse,
    AdminBookingListResponse,
    AdminInterviewerVerificationResponse,
    AdminPaymentItemResponse,
    AdminPaymentListResponse,
    AdminSlotItemResponse,
    AdminSlotListResponse,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserStatusUpdateRequest,
    AdminVerificationListResponse,
)
from app.services.audit import AuditService


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.interviewers = InterviewerRepository(session)
        self.bookings = BookingRepository(session)
        self.audit_service = AuditService(session)

    async def list_users(
        self,
        *,
        search: str | None = None,
        role: UserRole | None = None,
        status: UserStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminUserListResponse:
        users, total = await self.users.list_users(
            search=search,
            role=role,
            status=status,
            limit=limit,
            offset=offset,
        )
        return AdminUserListResponse(
            items=[AdminUserResponse.model_validate(u) for u in users],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_user(self, user_id: uuid.UUID) -> AdminUserResponse:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise ApiError("USER_NOT_FOUND", "User was not found.", 404)
        return AdminUserResponse.model_validate(user)

    async def update_user_status(
        self,
        user_id: uuid.UUID,
        admin: User,
        request: AdminUserStatusUpdateRequest,
    ) -> AdminUserResponse:
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise ApiError("USER_NOT_FOUND", "User was not found.", 404)

        if user.id == admin.id and request.status in (UserStatus.SUSPENDED, UserStatus.DISABLED):
            raise ApiError(
                "CANNOT_DISABLE_SELF",
                "Admins cannot disable or suspend themselves.",
                400,
            )

        old_status = user.status
        self.users.update_status(user, request.status)
        await self.audit_service.log_event(
            event_type="ADMIN_USER_STATUS_UPDATED",
            resource_type="USER",
            resource_id=str(user.id),
            actor_user_id=admin.id,
            metadata={
                "old_status": old_status.value,
                "new_status": request.status.value,
                "reason": request.reason,
            },
        )
        updated = await self.users.commit_and_refresh(user)
        return AdminUserResponse.model_validate(updated)

    async def list_verifications(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminVerificationListResponse:
        verifications, total = await self.interviewers.list_verifications(
            status=status,
            limit=limit,
            offset=offset,
        )
        items: list[AdminInterviewerVerificationResponse] = []
        for v in verifications:
            user = v.interviewer.user if v.interviewer else None
            items.append(
                AdminInterviewerVerificationResponse(
                    id=v.id,
                    interviewer_id=v.interviewer_id,
                    user_id=user.id if user else v.interviewer_id,
                    full_name=user.full_name if user else "Unknown",
                    email=user.email if user else "Unknown",
                    title=v.interviewer.title if v.interviewer else None,
                    years_experience=v.interviewer.years_experience if v.interviewer else None,
                    status=v.status.value if hasattr(v.status, "value") else str(v.status),
                    submitted_at=v.submitted_at,
                    reviewed_at=v.reviewed_at,
                    reviewed_by=v.reviewed_by,
                    notes=v.notes,
                )
            )
        return AdminVerificationListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_bookings(
        self,
        *,
        status: BookingStatus | None = None,
        candidate_id: uuid.UUID | None = None,
        interviewer_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminBookingListResponse:
        bookings, total = await self.bookings.list_admin_bookings(
            status=status,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            limit=limit,
            offset=offset,
        )
        items: list[AdminBookingItemResponse] = []
        for b in bookings:
            items.append(
                AdminBookingItemResponse(
                    id=b.id,
                    slot_id=b.slot_id,
                    candidate_id=b.candidate_id,
                    candidate_name=b.candidate.full_name if b.candidate else "Unknown",
                    candidate_email=b.candidate.email if b.candidate else "Unknown",
                    interviewer_id=b.interviewer_id,
                    interviewer_name=b.interviewer.full_name if b.interviewer else "Unknown",
                    interviewer_email=b.interviewer.email if b.interviewer else "Unknown",
                    status=b.status.value if hasattr(b.status, "value") else str(b.status),
                    cancellation_reason=None,
                    slot_start_time=b.slot.start_time if b.slot else b.created_at,
                    slot_end_time=b.slot.end_time if b.slot else b.created_at,
                    price_minor=b.price_minor,
                    currency=b.currency,
                    payment_status=(
                        b.payment.status.value
                        if b.payment and hasattr(b.payment.status, "value")
                        else (str(b.payment.status) if b.payment else None)
                    ),
                    created_at=b.created_at,
                )
            )
        return AdminBookingListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_booking_detail(self, booking_id: uuid.UUID) -> AdminBookingItemResponse:
        b = await self.bookings.get_booking_by_id(booking_id)
        if b is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking was not found.", 404)
        return AdminBookingItemResponse(
            id=b.id,
            slot_id=b.slot_id,
            candidate_id=b.candidate_id,
            candidate_name=b.candidate.full_name if b.candidate else "Unknown",
            candidate_email=b.candidate.email if b.candidate else "Unknown",
            interviewer_id=b.interviewer_id,
            interviewer_name=b.interviewer.full_name if b.interviewer else "Unknown",
            interviewer_email=b.interviewer.email if b.interviewer else "Unknown",
            status=b.status.value if hasattr(b.status, "value") else str(b.status),
            cancellation_reason=None,
            slot_start_time=b.slot.start_time if b.slot else b.created_at,
            slot_end_time=b.slot.end_time if b.slot else b.created_at,
            price_minor=b.price_minor,
            currency=b.currency,
            payment_status=(
                b.payment.status.value
                if b.payment and hasattr(b.payment.status, "value")
                else (str(b.payment.status) if b.payment else None)
            ),
            created_at=b.created_at,
        )

    async def list_payments(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminPaymentListResponse:
        payments, total = await self.bookings.list_admin_payments(
            status=status,
            limit=limit,
            offset=offset,
        )
        return AdminPaymentListResponse(
            items=[
                AdminPaymentItemResponse(
                    id=p.id,
                    booking_id=p.booking_id,
                    amount_minor=p.amount_minor,
                    currency=p.currency,
                    provider=p.provider,
                    status=p.status.value if hasattr(p.status, "value") else str(p.status),
                    provider_payment_id=p.provider_payment_id,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in payments
            ],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_slots(
        self,
        *,
        interviewer_id: uuid.UUID | None = None,
        status: AvailabilityStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AdminSlotListResponse:
        slots, total = await self.interviewers.list_admin_slots(
            interviewer_id=interviewer_id,
            status=status,
            limit=limit,
            offset=offset,
        )
        items: list[AdminSlotItemResponse] = []
        for s in slots:
            u = s.interviewer.user if s.interviewer else None
            items.append(
                AdminSlotItemResponse(
                    id=s.id,
                    interviewer_id=s.interviewer_id,
                    interviewer_name=u.full_name if u else "Unknown",
                    start_time=s.start_time,
                    end_time=s.end_time,
                    price_minor=s.price_minor,
                    currency=s.currency,
                    status=s.status.value if hasattr(s.status, "value") else str(s.status),
                    created_at=s.created_at,
                )
            )
        return AdminSlotListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
