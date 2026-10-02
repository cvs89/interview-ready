import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.integrations.payments import (
    WebhookSignatureVerificationError,
    get_payment_provider,
)
from app.models.availability import AvailabilityStatus
from app.models.booking import Booking, BookingStatus, Payment, PaymentStatus, PaymentWebhookEvent
from app.models.identity import User, UserRole
from app.repositories.bookings import BookingRepository
from app.repositories.interviewers import InterviewerRepository
from app.schemas.bookings import (
    BookingReserveRequest,
    BookingResponse,
    PaymentCheckoutRequest,
    PaymentCheckoutResponse,
    WebhookEventResponse,
)
from app.services.audit import AuditService
from app.services.notification import NotificationService


class BookingService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.booking_repo = BookingRepository(session)
        self.interviewer_repo = InterviewerRepository(session)
        self.audit_service = audit_service or AuditService(session)
        self.notification_service = notification_service or NotificationService(session)

    async def reserve_slot(self, user: User, request: BookingReserveRequest) -> BookingResponse:
        slot = await self.booking_repo.get_slot_for_update(request.slot_id)
        if slot is None:
            raise ApiError("SLOT_NOT_FOUND", "Availability slot not found.", 404)

        now = datetime.now(UTC)

        # Normalize expired reservation back to AVAILABLE before evaluating
        if (
            slot.status == AvailabilityStatus.RESERVED
            and slot.reservation_expires_at is not None
            and slot.reservation_expires_at <= now
        ):
            pending_booking = await self.booking_repo.get_booking_by_slot_id_for_update(slot.id)
            if pending_booking and pending_booking.status == BookingStatus.PENDING_PAYMENT:
                pending_booking.status = BookingStatus.EXPIRED
            slot.status = AvailabilityStatus.AVAILABLE
            slot.reserved_by = None
            slot.reservation_expires_at = None

        if slot.status == AvailabilityStatus.RESERVED:
            raise ApiError(
                "SLOT_ALREADY_RESERVED",
                "The selected slot is already reserved by another user.",
                409,
            )
        if slot.status == AvailabilityStatus.BOOKED:
            raise ApiError(
                "SLOT_ALREADY_BOOKED",
                "The selected slot is already booked.",
                409,
            )
        if slot.status != AvailabilityStatus.AVAILABLE:
            raise ApiError(
                "SLOT_UNAVAILABLE",
                "The selected slot is not available for reservation.",
                409,
            )

        if slot.start_time <= now:
            raise ApiError("SLOT_IN_PAST", "Cannot reserve an availability slot in the past.", 400)

        interviewer_profile = slot.interviewer
        if interviewer_profile is None:
            interviewer_profile = await self.interviewer_repo.get_profile_by_id(slot.interviewer_id)
        if interviewer_profile is None:
            raise ApiError("INTERVIEWER_NOT_FOUND", "Interviewer profile not found.", 404)

        if interviewer_profile.user_id == user.id:
            raise ApiError("CANNOT_BOOK_OWN_SLOT", "You cannot reserve your own slot.", 400)

        if not interviewer_profile.is_verified:
            raise ApiError(
                "INTERVIEWER_NOT_APPROVED",
                "Cannot reserve slot for an unverified interviewer.",
                400,
            )

        reservation_expires_at = now + timedelta(minutes=self.settings.reservation_ttl_minutes)
        slot.status = AvailabilityStatus.RESERVED
        slot.reserved_by = user.id
        slot.reservation_expires_at = reservation_expires_at

        booking = Booking(
            id=uuid.uuid4(),
            slot_id=slot.id,
            candidate_id=user.id,
            interviewer_id=interviewer_profile.user_id,
            status=BookingStatus.PENDING_PAYMENT,
            price_minor=slot.price_minor,
            currency=slot.currency,
        )
        self.session.add(booking)
        await self.audit_service.log_event(
            event_type="BOOKING_RESERVED",
            resource_type="BOOKING",
            resource_id=str(booking.id),
            actor_user_id=user.id,
            metadata={"slot_id": str(slot.id), "price_minor": booking.price_minor},
        )
        await self.session.commit()
        await self.session.refresh(booking)

        return self.to_booking_response(booking, reservation_expires_at=reservation_expires_at)

    async def get_booking(self, user: User, booking_id: uuid.UUID) -> BookingResponse:
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id not in (
            booking.candidate_id,
            booking.interviewer_id,
        ):
            raise ApiError("FORBIDDEN", "You do not have access to this booking.", 403)

        expires_at = booking.slot.reservation_expires_at if booking.slot else None
        return self.to_booking_response(booking, reservation_expires_at=expires_at)

    async def list_user_bookings(self, user: User) -> list[BookingResponse]:
        if user.role == UserRole.INTERVIEWER:
            bookings = await self.booking_repo.list_bookings_for_interviewer(user.id)
        else:
            bookings = await self.booking_repo.list_bookings_for_candidate(user.id)

        return [
            self.to_booking_response(
                b,
                reservation_expires_at=b.slot.reservation_expires_at if b.slot else None,
            )
            for b in bookings
        ]

    async def cancel_booking(
        self,
        user: User,
        booking_id: uuid.UUID,
        reason: str | None = None,
    ) -> BookingResponse:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id not in (
            booking.candidate_id,
            booking.interviewer_id,
        ):
            raise ApiError("FORBIDDEN", "You do not have permission to cancel this booking.", 403)

        if booking.status in (
            BookingStatus.CANCELLED,
            BookingStatus.COMPLETED,
            BookingStatus.REFUNDED,
        ):
            raise ApiError(
                "CANNOT_CANCEL_BOOKING",
                f"Booking is in status '{booking.status}' and cannot be cancelled.",
                400,
            )

        now = datetime.now(UTC)
        booking.status = BookingStatus.CANCELLED
        booking.cancelled_at = now

        slot = await self.booking_repo.get_slot_for_update(booking.slot_id)
        if slot:
            slot.status = AvailabilityStatus.AVAILABLE
            slot.reserved_by = None
            slot.reservation_expires_at = None

        await self.audit_service.log_event(
            event_type="BOOKING_CANCELLED",
            resource_type="BOOKING",
            resource_id=str(booking.id),
            actor_user_id=user.id,
            metadata={"slot_id": str(booking.slot_id), "reason": reason},
        )
        candidate = await self.session.get(User, booking.candidate_id)
        interviewer = await self.session.get(User, booking.interviewer_id)
        if candidate:
            await self.notification_service.dispatch_event(
                event_type="BOOKING_CANCELLED",
                recipient=candidate,
                title="Booking Cancelled",
                body=f"Your booking has been cancelled: {reason or 'User cancellation'}",
                data={"booking_id": str(booking.id)},
                reference_id=str(booking.id),
            )
        if interviewer:
            await self.notification_service.dispatch_event(
                event_type="BOOKING_CANCELLED",
                recipient=interviewer,
                title="Booking Cancelled",
                body=f"The booking has been cancelled: {reason or 'User cancellation'}",
                data={"booking_id": str(booking.id)},
                reference_id=str(booking.id),
            )

        await self.session.commit()
        return self.to_booking_response(booking, reservation_expires_at=None)

    async def expire_stale_reservations(self, now: datetime | None = None) -> int:
        now_utc = now or datetime.now(UTC)
        expired_count = 0

        # Expire slots that reached reservation expiry
        slots = await self.booking_repo.get_expired_slots(now_utc)
        for slot in slots:
            pending_booking = await self.booking_repo.get_booking_by_slot_id_for_update(slot.id)
            if pending_booking and pending_booking.status == BookingStatus.PENDING_PAYMENT:
                pending_booking.status = BookingStatus.EXPIRED
            slot.status = AvailabilityStatus.AVAILABLE
            slot.reserved_by = None
            slot.reservation_expires_at = None
            expired_count += 1

        # Expire any pending bookings that exceeded TTL cutoff
        cutoff = now_utc - timedelta(minutes=self.settings.reservation_ttl_minutes)
        pending_bookings = await self.booking_repo.get_pending_expired_bookings(cutoff)
        for booking in pending_bookings:
            booking.status = BookingStatus.EXPIRED
            if booking.slot and booking.slot.status == AvailabilityStatus.RESERVED:
                booking.slot.status = AvailabilityStatus.AVAILABLE
                booking.slot.reserved_by = None
                booking.slot.reservation_expires_at = None
            expired_count += 1

        if expired_count > 0:
            await self.session.commit()

        return expired_count

    @staticmethod
    def to_booking_response(
        booking: Booking,
        *,
        reservation_expires_at: datetime | None = None,
    ) -> BookingResponse:
        return BookingResponse(
            id=booking.id,
            slot_id=booking.slot_id,
            candidate_id=booking.candidate_id,
            interviewer_id=booking.interviewer_id,
            status=booking.status,
            price_minor=booking.price_minor,
            currency=booking.currency,
            reservation_expires_at=reservation_expires_at,
            created_at=booking.created_at,
            confirmed_at=booking.confirmed_at,
            started_at=booking.started_at,
            completed_at=booking.completed_at,
            cancelled_at=booking.cancelled_at,
        )


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.booking_repo = BookingRepository(session)
        self.audit_service = audit_service or AuditService(session)
        self.notification_service = notification_service or NotificationService(session)

    async def create_checkout(
        self,
        user: User,
        booking_id: uuid.UUID,
        request: PaymentCheckoutRequest,
        provider_name: str | None = None,
    ) -> PaymentCheckoutResponse:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if booking.candidate_id != user.id:
            raise ApiError("FORBIDDEN", "You do not have permission to pay for this booking.", 403)

        if booking.status == BookingStatus.CONFIRMED:
            raise ApiError("BOOKING_ALREADY_CONFIRMED", "This booking is already confirmed.", 409)

        if booking.status != BookingStatus.PENDING_PAYMENT:
            raise ApiError(
                "INVALID_BOOKING_STATUS",
                f"Booking is in status '{booking.status}' and cannot be paid.",
                400,
            )

        slot = await self.booking_repo.get_slot_for_update(booking.slot_id)
        now = datetime.now(UTC)

        # Check if slot reservation has expired
        if (
            slot is None
            or slot.status != AvailabilityStatus.RESERVED
            or (slot.reservation_expires_at and slot.reservation_expires_at <= now)
        ):
            booking.status = BookingStatus.EXPIRED
            if slot and slot.status == AvailabilityStatus.RESERVED:
                slot.status = AvailabilityStatus.AVAILABLE
                slot.reserved_by = None
                slot.reservation_expires_at = None
            await self.session.commit()
            raise ApiError(
                "RESERVATION_EXPIRED",
                "The reservation for this slot has expired. Please reserve again.",
                409,
            )

        provider = get_payment_provider(provider_name, self.settings)

        # Checkout amount must strictly come from the database Booking snapshot, never client
        checkout_result = await provider.create_checkout(
            booking_id=booking.id,
            candidate_id=booking.candidate_id,
            amount_minor=booking.price_minor,
            currency=booking.currency,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
        )

        payment = await self.booking_repo.get_payment_by_booking_id_for_update(booking.id)
        if payment is None:
            payment = Payment(
                id=uuid.uuid4(),
                booking_id=booking.id,
                candidate_id=booking.candidate_id,
                provider=provider.name,
                provider_checkout_session_id=checkout_result.checkout_session_id,
                provider_payment_id=checkout_result.provider_payment_id,
                amount_minor=booking.price_minor,
                currency=booking.currency,
                status=PaymentStatus.PENDING,
            )
            self.session.add(payment)
        else:
            if payment.status == PaymentStatus.PAID:
                raise ApiError(
                    "PAYMENT_ALREADY_COMPLETED",
                    "Payment has already been completed for this booking.",
                    409,
                )
            payment.provider = provider.name
            payment.provider_checkout_session_id = checkout_result.checkout_session_id
            payment.provider_payment_id = checkout_result.provider_payment_id
            payment.amount_minor = booking.price_minor
            payment.currency = booking.currency
            payment.status = PaymentStatus.PENDING

        await self.session.commit()

        return PaymentCheckoutResponse(
            booking_id=booking.id,
            payment_id=payment.id,
            provider=payment.provider,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            status=payment.status,
            checkout_url=checkout_result.checkout_url,
            provider_checkout_session_id=checkout_result.checkout_session_id,
            expires_at=slot.reservation_expires_at,
        )

    async def process_webhook(
        self,
        provider_name: str,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> WebhookEventResponse:
        try:
            provider = get_payment_provider(provider_name, self.settings)
        except ValueError:
            raise ApiError(
                "UNKNOWN_PAYMENT_PROVIDER",
                f"Unsupported payment provider: '{provider_name}'",
                404,
            ) from None

        try:
            event = await provider.verify_webhook(payload_bytes, headers)
        except WebhookSignatureVerificationError as exc:
            raise ApiError("INVALID_WEBHOOK_SIGNATURE", str(exc), 400) from exc

        # Webhook deduplication
        existing_event = await self.booking_repo.get_webhook_event(provider.name, event.event_id)
        if existing_event:
            return WebhookEventResponse(received=True, status="duplicate_ignored")

        now = datetime.now(UTC)
        webhook_event = PaymentWebhookEvent(
            id=uuid.uuid4(),
            provider=provider.name,
            provider_event_id=event.event_id,
            event_type=event.event_type,
            payload=event.payload,
            created_at=now,
        )
        self.session.add(webhook_event)

        # Row locking
        booking = await self.booking_repo.get_booking_by_id_for_update(event.booking_id)
        if booking is None:
            webhook_event.processed_at = now
            await self.session.commit()
            return WebhookEventResponse(received=True, status="booking_not_found")

        slot = await self.booking_repo.get_slot_for_update(booking.slot_id)
        payment = await self.booking_repo.get_payment_by_booking_id_for_update(booking.id)

        if event.status == PaymentStatus.PAID:
            # Verify amounts and currency against Booking snapshot
            if (
                event.amount_minor != booking.price_minor
                or event.currency.upper() != booking.currency.upper()
            ):
                if payment:
                    payment.status = PaymentStatus.FAILED
                webhook_event.processed_at = now
                await self.session.commit()
                raise ApiError(
                    "PAYMENT_AMOUNT_MISMATCH",
                    "Payment amount or currency mismatch against booking snapshot.",
                    400,
                )

            if booking.status == BookingStatus.CONFIRMED:
                if payment:
                    payment.status = PaymentStatus.PAID
                    payment.paid_at = payment.paid_at or now
                webhook_event.processed_at = now
                await self.session.commit()
                return WebhookEventResponse(received=True, status="already_confirmed")

            if payment is None:
                payment = Payment(
                    id=uuid.uuid4(),
                    booking_id=booking.id,
                    candidate_id=booking.candidate_id,
                    provider=provider.name,
                    provider_payment_id=event.provider_payment_id,
                    amount_minor=event.amount_minor,
                    currency=event.currency,
                    status=PaymentStatus.PAID,
                    paid_at=now,
                )
                self.session.add(payment)
            else:
                payment.status = PaymentStatus.PAID
                payment.paid_at = now
                if event.provider_payment_id:
                    payment.provider_payment_id = event.provider_payment_id

            booking.status = BookingStatus.CONFIRMED
            booking.confirmed_at = now

            if slot:
                slot.status = AvailabilityStatus.BOOKED
                slot.reserved_by = None
                slot.reservation_expires_at = None

            await self.audit_service.log_event(
                event_type="PAYMENT_PAID",
                resource_type="PAYMENT",
                resource_id=str(payment.id),
                metadata={
                    "amount_minor": event.amount_minor,
                    "currency": event.currency,
                    "provider": provider.name,
                },
            )
            await self.audit_service.log_event(
                event_type="BOOKING_CONFIRMED",
                resource_type="BOOKING",
                resource_id=str(booking.id),
                metadata={"slot_id": str(booking.slot_id)},
            )
            candidate = await self.session.get(User, booking.candidate_id)
            interviewer = await self.session.get(User, booking.interviewer_id)
            if candidate:
                await self.notification_service.dispatch_event(
                    event_type="BOOKING_CONFIRMED",
                    recipient=candidate,
                    title="Booking Confirmed",
                    body="Your mock interview session has been confirmed.",
                    data={"booking_id": str(booking.id)},
                    reference_id=str(booking.id),
                )
            if interviewer:
                await self.notification_service.dispatch_event(
                    event_type="BOOKING_CONFIRMED",
                    recipient=interviewer,
                    title="New Interview Booking",
                    body="A candidate has booked an interview with you.",
                    data={"booking_id": str(booking.id)},
                    reference_id=str(booking.id),
                )

            webhook_event.processed_at = now
            await self.session.commit()
            return WebhookEventResponse(received=True, status="processed")

        elif event.status in (PaymentStatus.FAILED, PaymentStatus.CANCELLED):
            if payment:
                payment.status = event.status
            await self.audit_service.log_event(
                event_type="PAYMENT_FAILED",
                resource_type="PAYMENT",
                resource_id=str(payment.id) if payment else "unknown",
                metadata={"booking_id": str(booking.id), "status": event.status.value},
            )
            candidate = await self.session.get(User, booking.candidate_id)
            if candidate:
                await self.notification_service.dispatch_event(
                    event_type="PAYMENT_FAILED",
                    recipient=candidate,
                    title="Payment Failed",
                    body="Payment for your interview reservation failed.",
                    data={"booking_id": str(booking.id)},
                    reference_id=str(booking.id),
                )
            webhook_event.processed_at = now
            await self.session.commit()
            return WebhookEventResponse(
                received=True,
                status=f"payment_{event.status.value.lower()}",
            )

        else:
            webhook_event.processed_at = now
            await self.session.commit()
            return WebhookEventResponse(received=True, status="unhandled_event_status")

    async def refund_payment(
        self,
        user: User,
        booking_id: uuid.UUID,
        reason: str | None = None,
    ) -> Payment:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id not in (
            booking.candidate_id,
            booking.interviewer_id,
        ):
            raise ApiError("FORBIDDEN", "You do not have permission to refund this booking.", 403)

        payment = await self.booking_repo.get_payment_by_booking_id_for_update(booking.id)
        if payment is None or payment.status != PaymentStatus.PAID:
            raise ApiError("PAYMENT_NOT_REFUNDABLE", "No completed payment found to refund.", 400)

        provider = get_payment_provider(payment.provider, self.settings)
        if payment.provider_payment_id:
            await provider.refund(
                provider_payment_id=payment.provider_payment_id,
                amount_minor=payment.amount_minor,
                currency=payment.currency,
                reason=reason,
            )

        now = datetime.now(UTC)
        payment.status = PaymentStatus.REFUNDED
        payment.refunded_at = now
        booking.status = BookingStatus.REFUNDED

        slot = await self.booking_repo.get_slot_for_update(booking.slot_id)
        if slot and slot.status == AvailabilityStatus.BOOKED:
            slot.status = AvailabilityStatus.AVAILABLE

        await self.audit_service.log_event(
            event_type="PAYMENT_REFUNDED",
            resource_type="PAYMENT",
            resource_id=str(payment.id),
            actor_user_id=user.id,
            metadata={
                "booking_id": str(payment.booking_id),
                "amount_minor": payment.amount_minor,
                "reason": reason,
            },
        )

        await self.session.commit()
        return payment
