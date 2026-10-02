import uuid
from datetime import datetime
from typing import Any, cast

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import InAppNotification, NotificationDeliveryLog


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add_in_app(self, notification: InAppNotification) -> InAppNotification:
        self.session.add(notification)
        return notification

    async def get_in_app_by_id(self, notification_id: uuid.UUID) -> InAppNotification | None:
        result = await self.session.execute(
            select(InAppNotification).where(InAppNotification.id == notification_id)
        )
        return result.scalar_one_or_none()

    async def list_in_app_for_user(
        self,
        user_id: uuid.UUID,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[InAppNotification]:
        query = select(InAppNotification).where(InAppNotification.user_id == user_id)
        if unread_only:
            query = query.where(InAppNotification.read_at.is_(None))
        query = query.order_by(InAppNotification.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars())

    async def mark_in_app_read(self, notification_id: uuid.UUID, read_at: datetime) -> bool:
        result = await self.session.execute(
            update(InAppNotification)
            .where(InAppNotification.id == notification_id, InAppNotification.read_at.is_(None))
            .values(read_at=read_at)
        )
        cursor_result = cast(CursorResult[Any], result)
        return bool(cursor_result.rowcount > 0)

    async def mark_all_in_app_read(self, user_id: uuid.UUID, read_at: datetime) -> int:
        result = await self.session.execute(
            update(InAppNotification)
            .where(InAppNotification.user_id == user_id, InAppNotification.read_at.is_(None))
            .values(read_at=read_at)
        )
        cursor_result = cast(CursorResult[Any], result)
        return int(cursor_result.rowcount)

    async def get_delivery_log_by_idempotency_key(
        self, idempotency_key: str
    ) -> NotificationDeliveryLog | None:
        result = await self.session.execute(
            select(NotificationDeliveryLog).where(
                NotificationDeliveryLog.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()

    def add_delivery_log(self, log: NotificationDeliveryLog) -> NotificationDeliveryLog:
        self.session.add(log)
        return log
