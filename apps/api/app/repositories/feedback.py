import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.feedback import InterviewerReview, InterviewRubric


class RubricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> InterviewRubric | None:
        result = await self.session.execute(
            select(InterviewRubric)
            .where(InterviewRubric.booking_id == booking_id)
            .options(selectinload(InterviewRubric.booking))
        )
        return result.scalar_one_or_none()

    async def get_by_booking_id_for_update(self, booking_id: uuid.UUID) -> InterviewRubric | None:
        result = await self.session.execute(
            select(InterviewRubric)
            .where(InterviewRubric.booking_id == booking_id)
            .with_for_update()
            .options(selectinload(InterviewRubric.booking))
        )
        return result.scalar_one_or_none()

    def add(self, rubric: InterviewRubric) -> InterviewRubric:
        self.session.add(rubric)
        return rubric


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_booking_id(self, booking_id: uuid.UUID) -> InterviewerReview | None:
        result = await self.session.execute(
            select(InterviewerReview)
            .where(InterviewerReview.booking_id == booking_id)
            .options(selectinload(InterviewerReview.booking))
        )
        return result.scalar_one_or_none()

    async def get_by_booking_id_for_update(self, booking_id: uuid.UUID) -> InterviewerReview | None:
        result = await self.session.execute(
            select(InterviewerReview)
            .where(InterviewerReview.booking_id == booking_id)
            .with_for_update()
            .options(selectinload(InterviewerReview.booking))
        )
        return result.scalar_one_or_none()

    def add(self, review: InterviewerReview) -> InterviewerReview:
        self.session.add(review)
        return review

    async def get_rating_summary(self, interviewer_id: uuid.UUID) -> tuple[float | None, int]:
        result = await self.session.execute(
            select(
                func.avg(InterviewerReview.rating),
                func.count(InterviewerReview.id),
            ).where(InterviewerReview.interviewer_id == interviewer_id)
        )
        row = result.one()
        avg_rating = float(row[0]) if row[0] is not None else None
        total_reviews = int(row[1]) if row[1] is not None else 0
        return avg_rating, total_reviews

    async def list_for_interviewer(
        self, interviewer_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[InterviewerReview]:
        result = await self.session.execute(
            select(InterviewerReview)
            .where(InterviewerReview.interviewer_id == interviewer_id)
            .order_by(InterviewerReview.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars())
