import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApiError
from app.models.booking import BookingStatus
from app.models.feedback import InterviewerReview, InterviewRubric, RubricStatus
from app.models.identity import User, UserRole
from app.models.session import SessionStatus
from app.repositories.bookings import BookingRepository
from app.repositories.feedback import ReviewRepository, RubricRepository
from app.repositories.sessions import InterviewSessionRepository
from app.schemas.feedback import (
    CandidateFeedbackResponse,
    InterviewerRatingSummary,
    InterviewerRubricResponse,
    ReviewCreateRequest,
    ReviewResponse,
    RubricDraftRequest,
    RubricSubmitRequest,
)
from app.services.audit import AuditService
from app.services.notification import NotificationService


class RubricService:
    def __init__(
        self,
        session: AsyncSession,
        audit_service: AuditService | None = None,
        notification_service: NotificationService | None = None,
    ) -> None:
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.rubric_repo = RubricRepository(session)
        self.session_repo = InterviewSessionRepository(session)
        self.audit_service = audit_service or AuditService(session)
        self.notification_service = notification_service or NotificationService(session)

    async def save_draft(
        self, user: User, booking_id: uuid.UUID, request: RubricDraftRequest
    ) -> InterviewerRubricResponse:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.id != booking.interviewer_id:
            raise ApiError("FORBIDDEN", "Only the assigned interviewer can edit the rubric.", 403)

        if booking.status in (
            BookingStatus.CANCELLED,
            BookingStatus.REFUNDED,
            BookingStatus.EXPIRED,
        ):
            raise ApiError(
                "INVALID_BOOKING_STATUS",
                f"Cannot edit rubric for booking with status '{booking.status.value}'.",
                400,
            )

        rubric = await self.rubric_repo.get_by_booking_id_for_update(booking_id)
        if rubric is not None:
            if rubric.status in (RubricStatus.SUBMITTED, RubricStatus.LOCKED):
                raise ApiError("RUBRIC_LOCKED", "Submitted rubric cannot be modified.", 400)

            if request.technical_score is not None:
                rubric.technical_score = request.technical_score
            if request.problem_solving_score is not None:
                rubric.problem_solving_score = request.problem_solving_score
            if request.communication_score is not None:
                rubric.communication_score = request.communication_score
            if request.detailed_feedback is not None:
                rubric.detailed_feedback = request.detailed_feedback
            if request.action_items is not None:
                rubric.action_items = request.action_items
            if request.private_interviewer_notes is not None:
                rubric.private_interviewer_notes = request.private_interviewer_notes
            rubric.version += 1
        else:
            rubric = InterviewRubric(
                id=uuid.uuid4(),
                booking_id=booking_id,
                interviewer_id=user.id,
                technical_score=request.technical_score,
                problem_solving_score=request.problem_solving_score,
                communication_score=request.communication_score,
                detailed_feedback=request.detailed_feedback,
                action_items=request.action_items,
                private_interviewer_notes=request.private_interviewer_notes,
                status=RubricStatus.DRAFT,
                version=1,
            )
            self.rubric_repo.add(rubric)

        await self.session.commit()
        await self.session.refresh(rubric)
        return InterviewerRubricResponse.model_validate(rubric)

    async def submit_rubric(
        self, user: User, booking_id: uuid.UUID, request: RubricSubmitRequest
    ) -> InterviewerRubricResponse:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.id != booking.interviewer_id:
            raise ApiError("FORBIDDEN", "Only the assigned interviewer can submit the rubric.", 403)

        if booking.status in (
            BookingStatus.CANCELLED,
            BookingStatus.REFUNDED,
            BookingStatus.EXPIRED,
        ):
            raise ApiError(
                "INVALID_BOOKING_STATUS",
                f"Cannot submit rubric for booking with status '{booking.status.value}'.",
                400,
            )

        rubric = await self.rubric_repo.get_by_booking_id_for_update(booking_id)
        if rubric is not None and rubric.status in (RubricStatus.SUBMITTED, RubricStatus.LOCKED):
            raise ApiError("RUBRIC_ALREADY_SUBMITTED", "Rubric has already been submitted.", 400)

        now = datetime.now(UTC)

        if rubric is not None:
            rubric.technical_score = request.technical_score
            rubric.problem_solving_score = request.problem_solving_score
            rubric.communication_score = request.communication_score
            rubric.detailed_feedback = request.detailed_feedback
            rubric.action_items = request.action_items
            rubric.private_interviewer_notes = request.private_interviewer_notes
            rubric.status = RubricStatus.SUBMITTED
            rubric.submitted_at = now
            rubric.version += 1
        else:
            rubric = InterviewRubric(
                id=uuid.uuid4(),
                booking_id=booking_id,
                interviewer_id=user.id,
                technical_score=request.technical_score,
                problem_solving_score=request.problem_solving_score,
                communication_score=request.communication_score,
                detailed_feedback=request.detailed_feedback,
                action_items=request.action_items,
                private_interviewer_notes=request.private_interviewer_notes,
                status=RubricStatus.SUBMITTED,
                version=1,
                submitted_at=now,
            )
            self.rubric_repo.add(rubric)

        # Transition booking to COMPLETED
        if booking.status != BookingStatus.COMPLETED:
            booking.status = BookingStatus.COMPLETED
            booking.completed_at = now

        # Transition interview session to ENDED if active/ready
        session_model = await self.session_repo.get_by_booking_id_for_update(booking_id)
        if session_model is not None and session_model.status != SessionStatus.ENDED:
            session_model.status = SessionStatus.ENDED
            session_model.ended_at = now

        await self.audit_service.log_event(
            event_type="RUBRIC_SUBMITTED",
            resource_type="RUBRIC",
            resource_id=str(rubric.id),
            actor_user_id=user.id,
            metadata={"booking_id": str(booking_id), "technical_score": rubric.technical_score},
        )
        await self.audit_service.log_event(
            event_type="BOOKING_COMPLETED",
            resource_type="BOOKING",
            resource_id=str(booking.id),
            actor_user_id=user.id,
        )
        candidate = await self.session.get(User, booking.candidate_id)
        if candidate:
            await self.notification_service.dispatch_event(
                event_type="FEEDBACK_AVAILABLE",
                recipient=candidate,
                title="Interview Feedback Available",
                body="Your interviewer has submitted evaluation rubric and feedback.",
                data={"booking_id": str(booking.id)},
                reference_id=str(booking.id),
            )

        await self.session.commit()
        await self.session.refresh(rubric)
        return InterviewerRubricResponse.model_validate(rubric)

    async def get_interviewer_rubric(
        self, user: User, booking_id: uuid.UUID
    ) -> InterviewerRubricResponse:
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id != booking.interviewer_id:
            raise ApiError(
                "FORBIDDEN",
                "Only the assigned interviewer can view interviewer notes and rubric details.",
                403,
            )

        rubric = await self.rubric_repo.get_by_booking_id(booking_id)
        if rubric is None:
            raise ApiError("RUBRIC_NOT_FOUND", "Rubric not found for this booking.", 404)

        return InterviewerRubricResponse.model_validate(rubric)

    async def get_candidate_feedback(
        self, user: User, booking_id: uuid.UUID
    ) -> CandidateFeedbackResponse:
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id != booking.candidate_id:
            raise ApiError(
                "FORBIDDEN",
                "You are not authorized to view feedback for this booking.",
                403,
            )

        rubric = await self.rubric_repo.get_by_booking_id(booking_id)
        if rubric is None or rubric.status not in (RubricStatus.SUBMITTED, RubricStatus.LOCKED):
            raise ApiError(
                "FEEDBACK_NOT_READY",
                "Feedback has not been submitted yet for this booking.",
                404,
            )

        return CandidateFeedbackResponse.model_validate(rubric)


class ReviewService:
    def __init__(
        self,
        session: AsyncSession,
        audit_service: AuditService | None = None,
    ) -> None:
        self.session = session
        self.booking_repo = BookingRepository(session)
        self.review_repo = ReviewRepository(session)
        self.audit_service = audit_service or AuditService(session)

    async def create_review(
        self, user: User, booking_id: uuid.UUID, request: ReviewCreateRequest
    ) -> ReviewResponse:
        booking = await self.booking_repo.get_booking_by_id_for_update(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.id != booking.candidate_id:
            raise ApiError("FORBIDDEN", "Only the candidate can review this booking.", 403)

        if booking.status != BookingStatus.COMPLETED:
            raise ApiError(
                "BOOKING_NOT_COMPLETED",
                "Reviews can only be submitted for completed interviews.",
                400,
            )

        existing = await self.review_repo.get_by_booking_id_for_update(booking_id)
        if existing is not None:
            raise ApiError(
                "REVIEW_ALREADY_EXISTS",
                "A review has already been submitted for this booking.",
                409,
            )

        review = InterviewerReview(
            id=uuid.uuid4(),
            booking_id=booking.id,
            candidate_id=user.id,
            interviewer_id=booking.interviewer_id,
            rating=request.rating,
            review=request.review,
        )
        self.review_repo.add(review)

        await self.audit_service.log_event(
            event_type="REVIEW_CREATED",
            resource_type="REVIEW",
            resource_id=str(review.id),
            actor_user_id=user.id,
            metadata={"booking_id": str(booking_id), "rating": review.rating},
        )

        await self.session.commit()
        await self.session.refresh(review)
        return ReviewResponse.model_validate(review)

    async def get_interviewer_rating_summary(
        self, interviewer_id: uuid.UUID
    ) -> InterviewerRatingSummary:
        avg_rating, count = await self.review_repo.get_rating_summary(interviewer_id)
        rounded_avg = round(avg_rating, 2) if avg_rating is not None else None
        return InterviewerRatingSummary(
            interviewer_id=interviewer_id,
            average_rating=rounded_avg,
            total_reviews=count,
        )

    async def list_interviewer_reviews(
        self, interviewer_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[ReviewResponse]:
        reviews = await self.review_repo.list_for_interviewer(
            interviewer_id, limit=limit, offset=offset
        )
        return [ReviewResponse.model_validate(r) for r in reviews]
