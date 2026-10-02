import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.integrations.notifications import (
    InAppNotificationChannel,
    MockEmailNotificationChannel,
    MockFCMNotificationChannel,
    NotificationChannel,
)
from app.models.identity import User
from app.models.notification import NotificationDeliveryLog
from app.repositories.notification import NotificationRepository
from app.schemas.notification import InAppNotificationResponse


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
        email_channel: NotificationChannel | None = None,
        fcm_channel: NotificationChannel | None = None,
    ) -> None:
        self.session = session
        self.notification_repo = NotificationRepository(session)
        self.email_channel = email_channel or MockEmailNotificationChannel()
        self.fcm_channel = fcm_channel or MockFCMNotificationChannel()
        self.in_app_channel = InAppNotificationChannel(session)

    def _get_channel(self, channel_name: str) -> NotificationChannel | None:
        name = channel_name.upper()
        if name == "EMAIL":
            return self.email_channel
        if name == "FCM":
            return self.fcm_channel
        if name == "IN_APP":
            return self.in_app_channel
        return None

    async def dispatch_event(
        self,
        event_type: str,
        recipient: User,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
        reference_id: str | None = None,
        channels: list[str] | None = None,
    ) -> dict[str, str]:
        selected_channels = channels or ["EMAIL", "IN_APP"]
        payload_data = dict(data or {})
        payload_data["event_type"] = event_type
        if reference_id is not None:
            payload_data["reference_id"] = reference_id

        results: dict[str, str] = {}
        now = datetime.now(UTC)

        for channel_name in selected_channels:
            norm_channel = channel_name.upper()
            channel_impl = self._get_channel(norm_channel)
            if channel_impl is None:
                continue

            ref_part = reference_id or "none"
            idempotency_key = f"{event_type}:{norm_channel}:{ref_part}:{recipient.id}"

            # Check deduplication
            existing_log = await self.notification_repo.get_delivery_log_by_idempotency_key(
                idempotency_key
            )
            if existing_log is not None and existing_log.status == "SENT":
                results[norm_channel] = "DEDUPLICATED"
                continue

            try:
                success = await channel_impl.send(
                    recipient=recipient,
                    title=title,
                    body=body,
                    data=payload_data,
                )
                if success:
                    status_str = "SENT"
                    err_msg = None
                else:
                    status_str = "FAILED"
                    err_msg = "Channel returned false"
            except Exception as exc:
                status_str = "FAILED"
                err_msg = str(exc)

            if existing_log is None:
                delivery_log = NotificationDeliveryLog(
                    id=uuid.uuid4(),
                    recipient_user_id=recipient.id,
                    event_type=event_type,
                    channel=norm_channel,
                    reference_id=reference_id,
                    idempotency_key=idempotency_key,
                    status=status_str,
                    error_message=err_msg,
                    created_at=now,
                    delivered_at=now if status_str == "SENT" else None,
                )
                self.notification_repo.add_delivery_log(delivery_log)
            else:
                existing_log.status = status_str
                existing_log.error_message = err_msg
                existing_log.delivered_at = now if status_str == "SENT" else None

            results[norm_channel] = status_str

        await self.session.commit()
        return results

    async def list_in_app_notifications(
        self,
        user: User,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InAppNotificationResponse]:
        notifications = await self.notification_repo.list_in_app_for_user(
            user_id=user.id,
            unread_only=unread_only,
            limit=limit,
            offset=offset,
        )
        return [InAppNotificationResponse.model_validate(n) for n in notifications]

    async def mark_as_read(self, user: User, notification_id: uuid.UUID) -> bool:
        notification = await self.notification_repo.get_in_app_by_id(notification_id)
        if notification is None:
            raise ApiError("NOTIFICATION_NOT_FOUND", "Notification not found.", 404)
        if notification.user_id != user.id:
            raise ApiError("FORBIDDEN", "You are not authorized to update this notification.", 403)

        now = datetime.now(UTC)
        updated = await self.notification_repo.mark_in_app_read(notification_id, now)
        await self.session.commit()
        return updated

    async def mark_all_as_read(self, user: User) -> int:
        now = datetime.now(UTC)
        count = await self.notification_repo.mark_all_in_app_read(user.id, now)
        await self.session.commit()
        return count
