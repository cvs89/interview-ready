import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.availability import (
    AvailabilitySlot,
    AvailabilityStatus,
    InterviewerVerification,
    VerificationStatus,
)
from app.models.identity import InterviewerProfile, InterviewerSkill, Skill, User, UserRole
from app.repositories.interviewers import InterviewerRepository
from app.schemas.interviewers import (
    AvailabilitySlotCreateRequest,
    AvailabilitySlotUpdateRequest,
    InterviewerSkillRequest,
    InterviewerSkillResponse,
    ProfileResponse,
    ProfileUpsertRequest,
    SkillCreateRequest,
    VerificationReviewRequest,
)
from app.services.audit import AuditService


class InterviewerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InterviewerRepository(session)
        self.audit_service = AuditService(session)

    @staticmethod
    def to_profile_response(profile: InterviewerProfile) -> ProfileResponse:
        verification_status = (
            profile.verification.status if profile.verification else VerificationStatus.PENDING
        )
        skills = [
            InterviewerSkillResponse(
                id=link.skill.id,
                name=link.skill.name,
                slug=link.skill.slug,
                years_experience=link.years_experience,
            )
            for link in sorted(profile.skill_links, key=lambda item: item.skill.name)
        ]
        return ProfileResponse(
            id=profile.id,
            full_name=profile.user.full_name,
            bio=profile.bio,
            title=profile.title,
            years_experience=profile.years_experience,
            default_rate_minor=profile.default_rate_minor,
            currency=profile.currency,
            linkedin_url=profile.linkedin_url,
            is_verified=profile.is_verified,
            verification_status=verification_status,
            skills=skills,
        )

    async def create_profile(self, user: User, request: ProfileUpsertRequest) -> ProfileResponse:
        if await self.repository.get_profile_for_user(user.id):
            raise ApiError("PROFILE_ALREADY_EXISTS", "An interviewer profile already exists.", 409)
        profile = InterviewerProfile(user_id=user.id)
        self._apply_profile_updates(profile, request)
        self.session.add(profile)
        await self.session.flush()
        self.session.add(
            InterviewerVerification(
                interviewer_id=profile.id,
                status=VerificationStatus.PENDING,
                submitted_at=datetime.now(UTC),
            )
        )
        await self.session.commit()
        loaded = await self.repository.get_profile_for_user(user.id)
        if loaded is None:
            raise RuntimeError("Created profile could not be loaded")
        return self.to_profile_response(loaded)

    async def update_profile(self, user: User, request: ProfileUpsertRequest) -> ProfileResponse:
        profile = await self._owned_profile(user.id)
        self._apply_profile_updates(profile, request)
        await self.session.commit()
        loaded = await self.repository.get_profile_for_user(user.id)
        if loaded is None:
            raise RuntimeError("Updated profile could not be loaded")
        return self.to_profile_response(loaded)

    @staticmethod
    def _apply_profile_updates(profile: InterviewerProfile, request: ProfileUpsertRequest) -> None:
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)

    async def submit_verification(self, user: User) -> InterviewerVerification:
        profile = await self._owned_profile(user.id)
        verification = await self.repository.get_verification(profile.id)
        if verification is None:
            verification = InterviewerVerification(interviewer_id=profile.id)
            self.session.add(verification)
        if verification.status == VerificationStatus.APPROVED:
            raise ApiError("ALREADY_APPROVED", "This interviewer is already approved.", 409)
        verification.status = VerificationStatus.PENDING
        verification.submitted_at = datetime.now(UTC)
        verification.reviewed_at = None
        verification.reviewed_by = None
        verification.notes = None
        profile.is_verified = False
        await self.session.commit()
        await self.session.refresh(verification)
        return verification

    async def review_verification(
        self,
        interviewer_id: uuid.UUID,
        reviewer: User,
        request: VerificationReviewRequest,
    ) -> InterviewerVerification:
        profile = await self.repository.get_profile_by_id(interviewer_id)
        if profile is None:
            raise ApiError("PROFILE_NOT_FOUND", "Interviewer profile not found.", 404)
        verification = await self.repository.get_verification(profile.id)
        if verification is None:
            raise ApiError("VERIFICATION_NOT_FOUND", "Verification request not found.", 404)
        verification.status = VerificationStatus(request.status)
        verification.reviewed_at = datetime.now(UTC)
        verification.reviewed_by = reviewer.id
        verification.notes = request.notes
        approved = verification.status == VerificationStatus.APPROVED
        profile.is_verified = approved
        if approved:
            profile.user.role = UserRole.INTERVIEWER
        elif profile.user.role == UserRole.INTERVIEWER:
            profile.user.role = UserRole.CANDIDATE
        await self.audit_service.log_event(
            event_type="INTERVIEWER_VERIFICATION_REVIEWED",
            resource_type="INTERVIEWER_PROFILE",
            resource_id=str(profile.id),
            actor_user_id=reviewer.id,
            metadata={"status": request.status, "notes": request.notes},
        )
        await self.session.commit()
        await self.session.refresh(verification)
        return verification

    async def create_skill(self, request: SkillCreateRequest) -> Skill:
        if await self.repository.get_skill_by_slug(request.slug):
            raise ApiError("SKILL_ALREADY_EXISTS", "This skill already exists.", 409)
        skill = Skill(name=request.name.strip(), slug=request.slug)
        self.session.add(skill)
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ApiError("SKILL_ALREADY_EXISTS", "This skill already exists.", 409) from None
        await self.session.refresh(skill)
        return skill

    async def add_skill(self, user: User, request: InterviewerSkillRequest) -> ProfileResponse:
        profile = await self._owned_profile(user.id)
        skill = await self.repository.get_skill(request.skill_id)
        if skill is None:
            raise ApiError("SKILL_NOT_FOUND", "Skill not found.", 404)
        link = await self.repository.get_skill_link(profile.id, skill.id)
        if link:
            link.years_experience = request.years_experience
        else:
            self.session.add(
                InterviewerSkill(
                    interviewer_id=profile.id,
                    skill_id=skill.id,
                    years_experience=request.years_experience,
                )
            )
        await self.session.commit()
        loaded = await self.repository.get_profile_for_user(user.id)
        if loaded is None:
            raise RuntimeError("Profile could not be loaded")
        return self.to_profile_response(loaded)

    async def remove_skill(self, user: User, skill_id: uuid.UUID) -> None:
        profile = await self._owned_profile(user.id)
        link = await self.repository.get_skill_link(profile.id, skill_id)
        if link is None:
            raise ApiError("SKILL_NOT_FOUND", "Profile skill not found.", 404)
        await self.session.delete(link)
        await self.session.commit()

    async def create_slot(
        self, user: User, request: AvailabilitySlotCreateRequest
    ) -> AvailabilitySlot:
        profile = await self._approved_profile(user)
        price_minor = request.price_minor
        currency = request.currency
        if price_minor is None:
            price_minor = profile.default_rate_minor
            currency = profile.currency
        if price_minor is None or currency is None:
            raise ApiError(
                "PRICING_REQUIRED",
                "Set profile default pricing or provide slot pricing.",
                422,
            )
        await self._ensure_no_overlap(profile.id, request.start_time, request.end_time)
        slot = AvailabilitySlot(
            interviewer_id=profile.id,
            start_time=request.start_time,
            end_time=request.end_time,
            price_minor=price_minor,
            currency=currency,
            status=AvailabilityStatus.AVAILABLE,
        )
        self.session.add(slot)
        await self.audit_service.log_event(
            event_type="SLOT_CREATED",
            resource_type="AVAILABILITY_SLOT",
            resource_id=str(slot.id),
            actor_user_id=user.id,
            metadata={
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "price_minor": slot.price_minor,
            },
        )
        await self._commit_slot_change()
        await self.session.refresh(slot)
        return slot

    async def update_slot(
        self,
        user: User,
        slot_id: uuid.UUID,
        request: AvailabilitySlotUpdateRequest,
    ) -> AvailabilitySlot:
        slot = await self._owned_slot(user.id, slot_id)
        if slot.status != AvailabilityStatus.AVAILABLE:
            raise ApiError("SLOT_NOT_EDITABLE", "Only available slots can be updated.", 409)
        start_time = request.start_time or slot.start_time
        end_time = request.end_time or slot.end_time
        if end_time <= start_time:
            raise ApiError("INVALID_TIME_RANGE", "end_time must be after start_time.", 422)
        await self._ensure_no_overlap(
            slot.interviewer_id, start_time, end_time, exclude_slot_id=slot.id
        )
        slot.start_time = start_time
        slot.end_time = end_time
        if "price_minor" in request.model_fields_set:
            if request.price_minor is None or request.currency is None:
                raise ApiError("PRICING_REQUIRED", "Slot pricing is required.", 422)
            slot.price_minor = request.price_minor
            slot.currency = request.currency
        await self.audit_service.log_event(
            event_type="SLOT_UPDATED",
            resource_type="AVAILABILITY_SLOT",
            resource_id=str(slot.id),
            actor_user_id=user.id,
            metadata={
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "price_minor": slot.price_minor,
            },
        )
        await self._commit_slot_change()
        await self.session.refresh(slot)
        return slot

    async def block_slot(self, user: User, slot_id: uuid.UUID) -> AvailabilitySlot:
        slot = await self._owned_slot(user.id, slot_id)
        if slot.status != AvailabilityStatus.AVAILABLE:
            raise ApiError("SLOT_NOT_EDITABLE", "Reserved or booked slots cannot be blocked.", 409)
        slot.status = AvailabilityStatus.BLOCKED
        await self.audit_service.log_event(
            event_type="SLOT_BLOCKED",
            resource_type="AVAILABILITY_SLOT",
            resource_id=str(slot.id),
            actor_user_id=user.id,
            metadata={"status": slot.status.value},
        )
        await self.session.commit()
        await self.session.refresh(slot)
        return slot

    async def _commit_slot_change(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise ApiError(
                "SLOT_OVERLAP", "This time overlaps another availability slot.", 409
            ) from None

    async def _ensure_no_overlap(
        self,
        interviewer_id: uuid.UUID,
        start_time: datetime,
        end_time: datetime,
        *,
        exclude_slot_id: uuid.UUID | None = None,
    ) -> None:
        if await self.repository.has_overlap(
            interviewer_id,
            start_time,
            end_time,
            exclude_slot_id=exclude_slot_id,
        ):
            raise ApiError("SLOT_OVERLAP", "This time overlaps another availability slot.", 409)

    async def _owned_profile(self, user_id: uuid.UUID) -> InterviewerProfile:
        profile = await self.repository.get_profile_for_user(user_id)
        if profile is None:
            raise ApiError("PROFILE_NOT_FOUND", "Interviewer profile not found.", 404)
        return profile

    async def _approved_profile(self, user: User) -> InterviewerProfile:
        profile = await self._owned_profile(user.id)
        if user.role != UserRole.INTERVIEWER or not profile.is_verified:
            raise ApiError(
                "INTERVIEWER_NOT_APPROVED",
                "Only approved interviewers can publish availability.",
                403,
            )
        return profile

    async def _owned_slot(self, user_id: uuid.UUID, slot_id: uuid.UUID) -> AvailabilitySlot:
        slot = await self.repository.get_owned_slot(slot_id, user_id)
        if slot is None:
            raise ApiError("SLOT_NOT_FOUND", "Availability slot not found.", 404)
        return slot
