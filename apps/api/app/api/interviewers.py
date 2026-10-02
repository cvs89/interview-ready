import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.errors import ApiError
from app.core.rate_limit import RateLimiter
from app.db.session import get_session
from app.models.identity import User, UserRole
from app.repositories.interviewers import InterviewerRepository
from app.schemas.interviewers import (
    AvailabilitySlotCreateRequest,
    AvailabilitySlotResponse,
    AvailabilitySlotUpdateRequest,
    InterviewerSkillRequest,
    ProfileResponse,
    ProfileUpsertRequest,
    SkillCreateRequest,
    SkillResponse,
    VerificationResponse,
    VerificationReviewRequest,
)
from app.services.interviewers import InterviewerService

router = APIRouter(tags=["interviewers"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]


@router.post(
    "/interviewers/me/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    request: ProfileUpsertRequest, user: CurrentUser, session: Session
) -> ProfileResponse:
    return await InterviewerService(session).create_profile(user, request)


@router.get("/interviewers/me/profile", response_model=ProfileResponse)
async def get_own_profile(user: CurrentUser, session: Session) -> ProfileResponse:
    profile = await InterviewerRepository(session).get_profile_for_user(user.id)
    if profile is None:
        raise ApiError("PROFILE_NOT_FOUND", "Interviewer profile not found.", 404)
    return InterviewerService.to_profile_response(profile)


@router.patch("/interviewers/me/profile", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpsertRequest, user: CurrentUser, session: Session
) -> ProfileResponse:
    return await InterviewerService(session).update_profile(user, request)


@router.post("/interviewers/me/verification", response_model=VerificationResponse)
async def submit_verification(user: CurrentUser, session: Session) -> VerificationResponse:
    return VerificationResponse.model_validate(
        await InterviewerService(session).submit_verification(user)
    )


@router.post("/interviewers/me/skills", response_model=ProfileResponse)
async def add_skill(
    request: InterviewerSkillRequest, user: CurrentUser, session: Session
) -> ProfileResponse:
    return await InterviewerService(session).add_skill(user, request)


@router.delete("/interviewers/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_skill(skill_id: uuid.UUID, user: CurrentUser, session: Session) -> Response:
    await InterviewerService(session).remove_skill(user, skill_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/interviewers/me/slots",
    response_model=AvailabilitySlotResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_slot(
    request: AvailabilitySlotCreateRequest, user: CurrentUser, session: Session
) -> AvailabilitySlotResponse:
    return AvailabilitySlotResponse.model_validate(
        await InterviewerService(session).create_slot(user, request)
    )


@router.patch("/interviewers/me/slots/{slot_id}", response_model=AvailabilitySlotResponse)
async def update_slot(
    slot_id: uuid.UUID,
    request: AvailabilitySlotUpdateRequest,
    user: CurrentUser,
    session: Session,
) -> AvailabilitySlotResponse:
    return AvailabilitySlotResponse.model_validate(
        await InterviewerService(session).update_slot(user, slot_id, request)
    )


@router.delete("/interviewers/me/slots/{slot_id}", response_model=AvailabilitySlotResponse)
async def block_slot(
    slot_id: uuid.UUID, user: CurrentUser, session: Session
) -> AvailabilitySlotResponse:
    return AvailabilitySlotResponse.model_validate(
        await InterviewerService(session).block_slot(user, slot_id)
    )


@router.get("/interviewers/me/slots", response_model=list[AvailabilitySlotResponse])
async def list_own_slots(user: CurrentUser, session: Session) -> list[AvailabilitySlotResponse]:
    slots = await InterviewerRepository(session).list_owned_slots(user.id)
    return [AvailabilitySlotResponse.model_validate(slot) for slot in slots]


@router.get("/skills", response_model=list[SkillResponse])
async def list_skills(session: Session) -> list[SkillResponse]:
    skills = await InterviewerRepository(session).list_skills()
    return [SkillResponse.model_validate(skill) for skill in skills]


@router.get(
    "/interviewers",
    response_model=list[ProfileResponse],
    dependencies=[Depends(RateLimiter(action="search_interviewers", limit=60, window_seconds=60))],
)
async def discover_interviewers(
    session: Session,
    skill: str | None = None,
    min_years_experience: Annotated[int | None, Query(ge=0)] = None,
    min_price_minor: Annotated[int | None, Query(ge=0)] = None,
    max_price_minor: Annotated[int | None, Query(ge=0)] = None,
    available_from: datetime | None = None,
    available_to: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ProfileResponse]:
    _validate_discovery_range(min_price_minor, max_price_minor, available_from, available_to)
    profiles = await InterviewerRepository(session).list_public_profiles(
        skill_slug=skill,
        min_years_experience=min_years_experience,
        min_price_minor=min_price_minor,
        max_price_minor=max_price_minor,
        available_from=available_from,
        available_to=available_to,
        limit=limit,
        offset=offset,
    )
    return [InterviewerService.to_profile_response(profile) for profile in profiles]


@router.get("/interviewers/{interviewer_id}", response_model=ProfileResponse)
async def get_public_profile(interviewer_id: uuid.UUID, session: Session) -> ProfileResponse:
    profile = await InterviewerRepository(session).get_public_profile(interviewer_id)
    if profile is None:
        raise ApiError("PROFILE_NOT_FOUND", "Interviewer profile not found.", 404)
    return InterviewerService.to_profile_response(profile)


@router.get(
    "/interviewers/{interviewer_id}/slots",
    response_model=list[AvailabilitySlotResponse],
)
async def list_public_slots(
    interviewer_id: uuid.UUID, session: Session
) -> list[AvailabilitySlotResponse]:
    slots = await InterviewerRepository(session).list_public_slots(interviewer_id)
    return [AvailabilitySlotResponse.model_validate(slot) for slot in slots]


@admin_router.post("/skills", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    request: SkillCreateRequest, _: AdminUser, session: Session
) -> SkillResponse:
    return SkillResponse.model_validate(await InterviewerService(session).create_skill(request))


@admin_router.patch(
    "/interviewer-verifications/{interviewer_id}",
    response_model=VerificationResponse,
)
async def review_verification(
    interviewer_id: uuid.UUID,
    request: VerificationReviewRequest,
    admin: AdminUser,
    session: Session,
) -> VerificationResponse:
    verification = await InterviewerService(session).review_verification(
        interviewer_id, admin, request
    )
    return VerificationResponse.model_validate(verification)


def _validate_discovery_range(
    min_price_minor: int | None,
    max_price_minor: int | None,
    available_from: datetime | None,
    available_to: datetime | None,
) -> None:
    if (
        min_price_minor is not None
        and max_price_minor is not None
        and min_price_minor > max_price_minor
    ):
        raise ApiError("INVALID_PRICE_RANGE", "Minimum price exceeds maximum price.", 422)
    for value in (available_from, available_to):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ApiError("TIMEZONE_REQUIRED", "Availability filters require a timezone.", 422)
    if available_from and available_to and available_from >= available_to:
        raise ApiError("INVALID_TIME_RANGE", "Availability range is invalid.", 422)
