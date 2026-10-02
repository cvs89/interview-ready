import uuid
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import User
from app.models.notification import InAppNotification


class NotificationChannel(ABC):
    @property
    @abstractmethod
    def channel_name(self) -> str:
        pass

    @abstractmethod
    async def send(
        self,
        recipient: User,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> bool:
        pass


class MockEmailNotificationChannel(NotificationChannel):
    channel_name = "EMAIL"

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []

    async def send(
        self,
        recipient: User,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> bool:
        self.sent_messages.append(
            {
                "recipient_id": recipient.id,
                "email": recipient.email,
                "title": title,
                "body": body,
                "data": data,
            }
        )
        return True


class MockFCMNotificationChannel(NotificationChannel):
    channel_name = "FCM"

    def __init__(self) -> None:
        self.sent_messages: list[dict[str, Any]] = []

    async def send(
        self,
        recipient: User,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> bool:
        self.sent_messages.append(
            {
                "recipient_id": recipient.id,
                "firebase_uid": recipient.firebase_uid,
                "title": title,
                "body": body,
                "data": data,
            }
        )
        return True


class InAppNotificationChannel(NotificationChannel):
    channel_name = "IN_APP"

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def send(
        self,
        recipient: User,
        title: str,
        body: str,
        data: dict[str, Any],
    ) -> bool:
        event_type = data.get("event_type", "GENERAL")
        notification = InAppNotification(
            id=uuid.uuid4(),
            user_id=recipient.id,
            event_type=event_type,
            title=title,
            body=body,
            data=data,
        )
        self.session.add(notification)
        return True
