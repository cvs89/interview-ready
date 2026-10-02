import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.feedback import RubricStatus


class RubricDraftRequest(BaseModel):
    technical_score: int | None = Field(None, ge=1, le=5)
    problem_solving_score: int | None = Field(None, ge=1, le=5)
    communication_score: int | None = Field(None, ge=1, le=5)
    detailed_feedback: str | None = None
    action_items: str | None = None
    private_interviewer_notes: str | None = None


class RubricSubmitRequest(BaseModel):
    technical_score: int = Field(..., ge=1, le=5)
    problem_solving_score: int = Field(..., ge=1, le=5)
    communication_score: int = Field(..., ge=1, le=5)
    detailed_feedback: str = Field(..., min_length=1)
    action_items: str | None = None
    private_interviewer_notes: str | None = None


class InterviewerRubricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    interviewer_id: uuid.UUID
    technical_score: int | None = None
    problem_solving_score: int | None = None
    communication_score: int | None = None
    detailed_feedback: str | None = None
    action_items: str | None = None
    private_interviewer_notes: str | None = None
    status: RubricStatus
    version: int
    submitted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class CandidateFeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: uuid.UUID
    technical_score: int | None = None
    problem_solving_score: int | None = None
    communication_score: int | None = None
    detailed_feedback: str | None = None
    action_items: str | None = None
    submitted_at: datetime | None = None
    status: RubricStatus


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    booking_id: uuid.UUID
    candidate_id: uuid.UUID
    interviewer_id: uuid.UUID
    rating: int
    review: str | None = None
    created_at: datetime


class InterviewerRatingSummary(BaseModel):
    interviewer_id: uuid.UUID
    average_rating: float | None = None
    total_reviews: int = 0
