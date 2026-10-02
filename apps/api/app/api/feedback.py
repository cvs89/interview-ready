import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.db.session import get_session
from app.models.identity import User
from app.schemas.feedback import (
    CandidateFeedbackResponse,
    InterviewerRatingSummary,
    InterviewerRubricResponse,
    ReviewCreateRequest,
    ReviewResponse,
    RubricDraftRequest,
    RubricSubmitRequest,
)
from app.services.feedback import ReviewService, RubricService

feedback_router = APIRouter(prefix="/bookings", tags=["feedback", "rubrics", "reviews"])
reviews_router = APIRouter(prefix="/interviewers", tags=["reviews"])

Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@feedback_router.post(
    "/{booking_id}/rubric/draft",
    response_model=InterviewerRubricResponse,
    status_code=status.HTTP_200_OK,
)
async def save_rubric_draft(
    booking_id: uuid.UUID,
    request: RubricDraftRequest,
    user: CurrentUser,
    session: Session,
) -> InterviewerRubricResponse:
    return await RubricService(session).save_draft(user, booking_id, request)


@feedback_router.post(
    "/{booking_id}/rubric/submit",
    response_model=InterviewerRubricResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_rubric(
    booking_id: uuid.UUID,
    request: RubricSubmitRequest,
    user: CurrentUser,
    session: Session,
) -> InterviewerRubricResponse:
    return await RubricService(session).submit_rubric(user, booking_id, request)


@feedback_router.get(
    "/{booking_id}/rubric",
    response_model=InterviewerRubricResponse,
)
async def get_interviewer_rubric(
    booking_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
) -> InterviewerRubricResponse:
    return await RubricService(session).get_interviewer_rubric(user, booking_id)


@feedback_router.get(
    "/{booking_id}/feedback",
    response_model=CandidateFeedbackResponse,
)
async def get_candidate_feedback(
    booking_id: uuid.UUID,
    user: CurrentUser,
    session: Session,
) -> CandidateFeedbackResponse:
    return await RubricService(session).get_candidate_feedback(user, booking_id)


@feedback_router.post(
    "/{booking_id}/review",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    booking_id: uuid.UUID,
    request: ReviewCreateRequest,
    user: CurrentUser,
    session: Session,
) -> ReviewResponse:
    return await ReviewService(session).create_review(user, booking_id, request)


@reviews_router.get(
    "/{interviewer_id}/rating",
    response_model=InterviewerRatingSummary,
)
async def get_interviewer_rating_summary(
    interviewer_id: uuid.UUID,
    session: Session,
) -> InterviewerRatingSummary:
    return await ReviewService(session).get_interviewer_rating_summary(interviewer_id)


@reviews_router.get(
    "/{interviewer_id}/reviews",
    response_model=list[ReviewResponse],
)
async def list_interviewer_reviews(
    interviewer_id: uuid.UUID,
    session: Session,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ReviewResponse]:
    return await ReviewService(session).list_interviewer_reviews(
        interviewer_id, limit=limit, offset=offset
    )
