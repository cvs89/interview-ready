import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import InterviewSession


class InterviewSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> InterviewSession | None:
        result = await self.session.execute(
            select(InterviewSession)
            .where(InterviewSession.booking_id == booking_id)
            .options(selectinload(InterviewSession.booking))
        )
        return result.scalar_one_or_none()

    async def get_by_booking_id_for_update(self, booking_id: uuid.UUID) -> InterviewSession | None:
        result = await self.session.execute(
            select(InterviewSession)
            .where(InterviewSession.booking_id == booking_id)
            .with_for_update()
            .options(selectinload(InterviewSession.booking))
        )
        return result.scalar_one_or_none()

    async def get_by_room_name(self, room_name: str) -> InterviewSession | None:
        result = await self.session.execute(
            select(InterviewSession)
            .where(InterviewSession.livekit_room_name == room_name)
            .options(selectinload(InterviewSession.booking))
        )
        return result.scalar_one_or_none()
