from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.models.booking import Booking, BookingStatus
from app.models.identity import User
from app.schemas.notification import TaskProcessResponse
from app.services.audit import AuditService
from app.services.bookings import BookingService
from app.services.notification import NotificationService


class TaskService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.audit_service = AuditService(session)
        self.notification_service = notification_service or NotificationService(session)

    async def process_task(self, task_type: str, payload: dict[str, Any]) -> TaskProcessResponse:
        norm_type = task_type.strip().lower()
        if norm_type == "expire_reservations":
            return await self._process_expire_reservations()
        if norm_type == "send_reminders":
            return await self._process_send_reminders()
        if norm_type == "dispatch_notification":
            return await self._process_dispatch_notification(payload)
        if norm_type == "post_interview_reminders":
            return await self._process_post_interview_reminders()

        raise ApiError("UNKNOWN_TASK_TYPE", f"Task type '{task_type}' is not recognized.", 400)

    async def _process_expire_reservations(self) -> TaskProcessResponse:
        booking_service = BookingService(self.session, self.settings)
        count = await booking_service.expire_stale_reservations()
        if count > 0:
            await self.audit_service.log_event(
                event_type="RESERVATION_EXPIRED_BATCH",
                resource_type="BOOKINGS",
                resource_id="system",
                metadata={"expired_count": count},
            )
            await self.session.commit()
        return TaskProcessResponse(
            task_type="expire_reservations",
            processed_count=count,
            details={"expired_count": count},
        )

    async def _process_send_reminders(self) -> TaskProcessResponse:
        now = datetime.now(UTC)
        # Fetch upcoming confirmed bookings
        result = await self.session.execute(
            select(Booking)
            .where(Booking.status == BookingStatus.CONFIRMED)
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.candidate),
                selectinload(Booking.interviewer),
            )
        )
        bookings = list(result.scalars())
        processed = 0

        for b in bookings:
            start = b.slot.start_time
            time_until_start = start - now

            # 24 hour window
            if timedelta(hours=23) <= time_until_start <= timedelta(hours=24, minutes=15):
                await self._send_booking_reminder(b, "REMINDER_24H", "Interview in 24 hours")
                processed += 1

            # 1 hour window
            elif timedelta(minutes=50) <= time_until_start <= timedelta(hours=1, minutes=10):
                await self._send_booking_reminder(b, "REMINDER_1H", "Interview in 1 hour")
                processed += 1

            # 10 minute window
            elif timedelta(seconds=0) <= time_until_start <= timedelta(minutes=15):
                await self._send_booking_reminder(b, "REMINDER_10M", "Interview starting soon")
                processed += 1

        return TaskProcessResponse(
            task_type="send_reminders",
            processed_count=processed,
            details={"reminders_checked": len(bookings), "reminders_sent": processed},
        )

    async def _send_booking_reminder(self, booking: Booking, event_type: str, title: str) -> None:
        body = f"Your interview session is scheduled for {booking.slot.start_time.isoformat()}."
        data = {
            "booking_id": str(booking.id),
            "start_time": booking.slot.start_time.isoformat(),
        }

        # Send to candidate
        await self.notification_service.dispatch_event(
            event_type=event_type,
            recipient=booking.candidate,
            title=title,
            body=body,
            data=data,
            reference_id=str(booking.id),
        )
        # Send to interviewer
        await self.notification_service.dispatch_event(
            event_type=event_type,
            recipient=booking.interviewer,
            title=title,
            body=body,
            data=data,
            reference_id=str(booking.id),
        )

    async def _process_dispatch_notification(self, payload: dict[str, Any]) -> TaskProcessResponse:
        recipient_id = payload.get("recipient_user_id")
        event_type = payload.get("event_type", "GENERAL")
        title = payload.get("title", "Notification")
        body = payload.get("body", "")
        data = payload.get("data", {})
        reference_id = payload.get("reference_id")
        channels = payload.get("channels")

        if not recipient_id:
            raise ApiError("INVALID_PAYLOAD", "Missing recipient_user_id.", 400)

        recipient = await self.session.get(User, recipient_id)
        if recipient is None:
            raise ApiError("USER_NOT_FOUND", "Recipient user not found.", 404)

        results = await self.notification_service.dispatch_event(
            event_type=event_type,
            recipient=recipient,
            title=title,
            body=body,
            data=data,
            reference_id=reference_id,
            channels=channels,
        )
        return TaskProcessResponse(
            task_type="dispatch_notification",
            processed_count=1,
            details={"channels": results},
        )

    async def _process_post_interview_reminders(self) -> TaskProcessResponse:
        # Scan completed bookings where feedback was submitted
        return TaskProcessResponse(
            task_type="post_interview_reminders",
            processed_count=0,
            details={},
        )
