import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.booking import Booking, BookingStatus, Payment, PaymentWebhookEvent


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_slot_for_update(self, slot_id: uuid.UUID) -> AvailabilitySlot | None:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .where(AvailabilitySlot.id == slot_id)
            .with_for_update()
            .options(selectinload(AvailabilitySlot.interviewer))
        )
        return result.scalar_one_or_none()

    async def get_slot_by_id(self, slot_id: uuid.UUID) -> AvailabilitySlot | None:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .where(AvailabilitySlot.id == slot_id)
            .options(selectinload(AvailabilitySlot.interviewer))
        )
        return result.scalar_one_or_none()

    async def get_booking_by_id(self, booking_id: uuid.UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.payment),
                selectinload(Booking.interview_session),
                selectinload(Booking.candidate),
                selectinload(Booking.interviewer),
            )
        )
        return result.scalar_one_or_none()

    async def get_booking_by_id_for_update(self, booking_id: uuid.UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.payment),
                selectinload(Booking.interview_session),
                selectinload(Booking.candidate),
                selectinload(Booking.interviewer),
            )
        )
        return result.scalar_one_or_none()

    async def get_booking_by_slot_id_for_update(self, slot_id: uuid.UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.slot_id == slot_id)
            .with_for_update()
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.payment),
                selectinload(Booking.interview_session),
            )
        )
        return result.scalar_one_or_none()

    async def list_bookings_for_candidate(self, candidate_id: uuid.UUID) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.candidate_id == candidate_id)
            .order_by(Booking.created_at.desc())
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.payment),
                selectinload(Booking.interview_session),
            )
        )
        return list(result.scalars())

    async def list_bookings_for_interviewer(self, interviewer_id: uuid.UUID) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(Booking.interviewer_id == interviewer_id)
            .order_by(Booking.created_at.desc())
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.payment),
                selectinload(Booking.interview_session),
            )
        )
        return list(result.scalars())

    async def get_payment_by_booking_id(self, booking_id: uuid.UUID) -> Payment | None:
        result = await self.session.execute(select(Payment).where(Payment.booking_id == booking_id))
        return result.scalar_one_or_none()

    async def get_payment_by_booking_id_for_update(self, booking_id: uuid.UUID) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.booking_id == booking_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_payment_by_provider_payment_id(self, provider_payment_id: str) -> Payment | None:
        result = await self.session.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        return result.scalar_one_or_none()

    async def get_webhook_event(
        self, provider: str, provider_event_id: str
    ) -> PaymentWebhookEvent | None:
        result = await self.session.execute(
            select(PaymentWebhookEvent).where(
                PaymentWebhookEvent.provider == provider,
                PaymentWebhookEvent.provider_event_id == provider_event_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_expired_slots(self, now: datetime) -> list[AvailabilitySlot]:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .where(
                AvailabilitySlot.status == AvailabilityStatus.RESERVED,
                AvailabilitySlot.reservation_expires_at <= now,
            )
            .with_for_update()
        )
        return list(result.scalars())

    async def get_pending_expired_bookings(self, cutoff: datetime) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .where(
                Booking.status == BookingStatus.PENDING_PAYMENT,
                Booking.created_at <= cutoff,
            )
            .with_for_update()
            .options(selectinload(Booking.slot), selectinload(Booking.payment))
        )
        return list(result.scalars())

    async def list_admin_bookings(
        self,
        *,
        status: BookingStatus | None = None,
        candidate_id: uuid.UUID | None = None,
        interviewer_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Booking], int]:
        filters = []
        if status is not None:
            filters.append(Booking.status == status)
        if candidate_id is not None:
            filters.append(Booking.candidate_id == candidate_id)
        if interviewer_id is not None:
            filters.append(Booking.interviewer_id == interviewer_id)

        from sqlalchemy import func

        count_stmt = select(func.count(Booking.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(Booking).options(
            selectinload(Booking.slot),
            selectinload(Booking.payment),
            selectinload(Booking.interview_session),
            selectinload(Booking.candidate),
            selectinload(Booking.interviewer),
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(Booking.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars()), total_count

    async def list_admin_payments(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Payment], int]:
        from sqlalchemy import func

        filters = []
        if status is not None:
            filters.append(Payment.status == status)

        count_stmt = select(func.count(Payment.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(Payment)
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(Payment.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars()), total_count
