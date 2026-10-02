import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.availability import (
    AvailabilitySlot,
    AvailabilityStatus,
    InterviewerVerification,
)
from app.models.identity import InterviewerProfile, InterviewerSkill, Skill, User, UserRole


class InterviewerRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _profile_load_options() -> tuple[Any, ...]:
        return (
            selectinload(InterviewerProfile.user),
            selectinload(InterviewerProfile.verification),
            selectinload(InterviewerProfile.skill_links).selectinload(InterviewerSkill.skill),
        )

    async def get_profile_for_user(self, user_id: uuid.UUID) -> InterviewerProfile | None:
        result = await self.session.execute(
            select(InterviewerProfile)
            .where(InterviewerProfile.user_id == user_id)
            .options(*self._profile_load_options())
        )
        return result.scalar_one_or_none()

    async def get_public_profile(self, interviewer_id: uuid.UUID) -> InterviewerProfile | None:
        result = await self.session.execute(
            select(InterviewerProfile)
            .where(
                InterviewerProfile.id == interviewer_id,
                InterviewerProfile.is_verified.is_(True),
                InterviewerProfile.user.has(User.role == UserRole.INTERVIEWER),
            )
            .options(*self._profile_load_options())
        )
        return result.scalar_one_or_none()

    async def list_public_profiles(
        self,
        *,
        skill_slug: str | None,
        min_years_experience: int | None,
        min_price_minor: int | None,
        max_price_minor: int | None,
        available_from: datetime | None,
        available_to: datetime | None,
        limit: int,
        offset: int,
    ) -> list[InterviewerProfile]:
        statement = select(InterviewerProfile).where(
            InterviewerProfile.is_verified.is_(True),
            InterviewerProfile.user.has(User.role == UserRole.INTERVIEWER),
        )
        if skill_slug:
            statement = statement.where(
                InterviewerProfile.skill_links.any(
                    InterviewerSkill.skill.has(Skill.slug == skill_slug)
                )
            )
        if min_years_experience is not None:
            statement = statement.where(InterviewerProfile.years_experience >= min_years_experience)

        slot_filters = [AvailabilitySlot.status == AvailabilityStatus.AVAILABLE]
        if min_price_minor is not None:
            slot_filters.append(AvailabilitySlot.price_minor >= min_price_minor)
        if max_price_minor is not None:
            slot_filters.append(AvailabilitySlot.price_minor <= max_price_minor)
        if available_from is not None:
            slot_filters.append(AvailabilitySlot.end_time > available_from)
        if available_to is not None:
            slot_filters.append(AvailabilitySlot.start_time < available_to)
        if any(
            value is not None
            for value in (
                min_price_minor,
                max_price_minor,
                available_from,
                available_to,
            )
        ):
            statement = statement.where(
                InterviewerProfile.availability_slots.any(and_(*slot_filters))
            )

        result = await self.session.execute(
            statement.options(*self._profile_load_options())
            .order_by(InterviewerProfile.created_at, InterviewerProfile.id)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().unique())

    async def get_profile_by_id(self, interviewer_id: uuid.UUID) -> InterviewerProfile | None:
        result = await self.session.execute(
            select(InterviewerProfile)
            .where(InterviewerProfile.id == interviewer_id)
            .options(*self._profile_load_options())
        )
        return result.scalar_one_or_none()

    async def get_skill(self, skill_id: uuid.UUID) -> Skill | None:
        return await self.session.get(Skill, skill_id)

    async def list_skills(self) -> list[Skill]:
        result = await self.session.execute(select(Skill).order_by(Skill.name))
        return list(result.scalars())

    async def get_skill_by_slug(self, slug: str) -> Skill | None:
        result = await self.session.execute(select(Skill).where(Skill.slug == slug))
        return result.scalar_one_or_none()

    async def get_skill_link(
        self, interviewer_id: uuid.UUID, skill_id: uuid.UUID
    ) -> InterviewerSkill | None:
        return await self.session.get(
            InterviewerSkill,
            {"interviewer_id": interviewer_id, "skill_id": skill_id},
        )

    async def get_owned_slot(
        self, slot_id: uuid.UUID, user_id: uuid.UUID
    ) -> AvailabilitySlot | None:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .join(InterviewerProfile)
            .where(
                AvailabilitySlot.id == slot_id,
                InterviewerProfile.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def has_overlap(
        self,
        interviewer_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        *,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> bool:
        statement = select(AvailabilitySlot.id).where(
            AvailabilitySlot.interviewer_id == interviewer_id,
            AvailabilitySlot.start_time < end_time,
            AvailabilitySlot.end_time > start_time,
        )
        if exclude_slot_id:
            statement = statement.where(AvailabilitySlot.id != exclude_slot_id)
        return (await self.session.execute(statement.limit(1))).scalar_one_or_none() is not None

    async def list_owned_slots(self, user_id: uuid.UUID) -> list[AvailabilitySlot]:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .join(InterviewerProfile)
            .where(InterviewerProfile.user_id == user_id)
            .order_by(AvailabilitySlot.start_time)
        )
        return list(result.scalars())

    async def list_public_slots(self, interviewer_id: uuid.UUID) -> list[AvailabilitySlot]:
        result = await self.session.execute(
            select(AvailabilitySlot)
            .join(InterviewerProfile)
            .where(
                AvailabilitySlot.interviewer_id == interviewer_id,
                InterviewerProfile.is_verified.is_(True),
                InterviewerProfile.user.has(User.role == UserRole.INTERVIEWER),
                AvailabilitySlot.status == AvailabilityStatus.AVAILABLE,
            )
            .order_by(AvailabilitySlot.start_time)
        )
        return list(result.scalars())

    async def get_verification(self, interviewer_id: uuid.UUID) -> InterviewerVerification | None:
        result = await self.session.execute(
            select(InterviewerVerification)
            .where(InterviewerVerification.interviewer_id == interviewer_id)
            .options(
                selectinload(InterviewerVerification.interviewer).selectinload(
                    InterviewerProfile.user
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_verifications(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[InterviewerVerification], int]:
        filters = []
        if status:
            filters.append(InterviewerVerification.status == status)

        count_stmt = select(func.count(InterviewerVerification.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(InterviewerVerification).options(
            selectinload(InterviewerVerification.interviewer).selectinload(InterviewerProfile.user)
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = (
            stmt.order_by(
                InterviewerVerification.submitted_at.desc().nulls_last(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars()), total_count

    async def list_admin_slots(
        self,
        *,
        interviewer_id: uuid.UUID | None = None,
        status: AvailabilityStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AvailabilitySlot], int]:
        filters = []
        if interviewer_id is not None:
            filters.append(AvailabilitySlot.interviewer_id == interviewer_id)
        if status is not None:
            filters.append(AvailabilitySlot.status == status)

        count_stmt = select(func.count(AvailabilitySlot.id))
        if filters:
            count_stmt = count_stmt.where(*filters)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(AvailabilitySlot).options(
            selectinload(AvailabilitySlot.interviewer).selectinload(InterviewerProfile.user)
        )
        if filters:
            stmt = stmt.where(*filters)
        stmt = stmt.order_by(AvailabilitySlot.start_time.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars()), total_count
