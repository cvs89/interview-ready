from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.common import BaseService, audit, authorize, new_doc, notify, now
from app.firestore_backend.store import Document, UnitOfWork
from app.schemas.feedback import CandidateFeedbackResponse, InterviewerRubricResponse


class RubricService(BaseService):
    async def save(
        self, user: Any, booking_id: object, request: Any, submit: bool = False
    ) -> InterviewerRubricResponse:
        async def operation(tx: UnitOfWork) -> Document:
            booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
            authorize(user, booking, "interviewer_id", admin=False)
            if booking["status"] not in ("CONFIRMED", "IN_PROGRESS"):
                raise ApiError("INVALID_BOOKING_STATUS", "Booking cannot be assessed.", 400)
            rubric = await tx.get("feedback", booking_id)
            notes = await tx.get("private_notes", booking_id)
            session = await tx.get("sessions", booking_id)
            if rubric and rubric["status"] != "DRAFT":
                raise ApiError("RUBRIC_LOCKED", "Submitted rubric cannot be edited.", 400)
            rubric = rubric or new_doc(
                booking_id=str(booking_id),
                interviewer_id=str(user.id),
                status="DRAFT",
                version=0,
                submitted_at=None,
            )
            changes = request.model_dump(exclude_unset=True)
            private = changes.pop("private_interviewer_notes", (notes or {}).get("text"))
            rubric.update(changes, version=rubric["version"] + 1, updated_at=now())
            if submit:
                rubric.update(status="SUBMITTED", submitted_at=now())
                booking.update(status="COMPLETED", completed_at=now())
                tx.put("bookings", booking_id, booking)
                if session:
                    session.update(status="ENDED", ended_at=now())
                    tx.put("sessions", booking_id, session)
                await notify(
                    tx,
                    "FEEDBACK_AVAILABLE",
                    booking["candidate_id"],
                    str(booking_id),
                    "Interview feedback available",
                    data={"booking_id": str(booking_id)},
                )
                audit(tx, "RUBRIC_SUBMITTED", "RUBRIC", rubric["id"], user.id)
                audit(tx, "BOOKING_COMPLETED", "BOOKING", booking_id, user.id)
            tx.put("feedback", booking_id, rubric)
            tx.put("private_notes", booking_id, {"interviewer_id": str(user.id), "text": private})
            return {**rubric, "private_interviewer_notes": private}

        return InterviewerRubricResponse.model_validate(await self.store.run(operation))

    async def save_draft(self, user: Any, booking_id: object, request: Any) -> Any:
        return await self.save(user, booking_id, request)

    async def submit_rubric(self, user: Any, booking_id: object, request: Any) -> Any:
        return await self.save(user, booking_id, request, submit=True)

    async def get_interviewer_rubric(self, user: Any, booking_id: object) -> Any:
        tx = self.store.reader()
        booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
        authorize(user, booking, "interviewer_id")
        rubric = await tx.require("feedback", booking_id, "RUBRIC_NOT_FOUND")
        notes = await tx.get("private_notes", booking_id)
        return InterviewerRubricResponse.model_validate(
            {**rubric, "private_interviewer_notes": (notes or {}).get("text")}
        )

    async def get_candidate_feedback(self, user: Any, booking_id: object) -> Any:
        tx = self.store.reader()
        booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
        authorize(user, booking, "candidate_id")
        rubric = await tx.require("feedback", booking_id, "FEEDBACK_NOT_FOUND")
        if rubric["status"] not in ("SUBMITTED", "LOCKED"):
            raise ApiError("FEEDBACK_NOT_AVAILABLE", "Feedback has not been submitted.", 404)
        # No private_notes read occurs on this path.
        return CandidateFeedbackResponse.model_validate(rubric)


class ReviewService(BaseService):
    async def create_review(self, user: Any, booking_id: object, request: Any) -> Document:
        async def operation(tx: UnitOfWork) -> Document:
            booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
            authorize(user, booking, "candidate_id", admin=False)
            if booking["status"] != "COMPLETED":
                raise ApiError("BOOKING_NOT_COMPLETED", "Complete the interview first.", 400)
            if await tx.get("reviews", booking_id):
                raise ApiError("REVIEW_ALREADY_EXISTS", "Review already submitted.", 409)
            # Preserve the user-ID review contract; also index by public profile
            # ID so marketplace callers can query using a profile URL.
            binding = await tx.require(
                "profile_keys", booking["interviewer_id"], "PROFILE_NOT_FOUND"
            )
            profile_id = binding["profile_id"]
            summary = await tx.get("ratings", profile_id) or {"sum": 0, "total_reviews": 0}
            review = new_doc(
                booking_id=str(booking_id),
                candidate_id=str(user.id),
                interviewer_id=booking["interviewer_id"],
                profile_id=profile_id,
                rating=request.rating,
                review=request.review,
            )
            summary["sum"] += request.rating
            summary["total_reviews"] += 1
            tx.put("ratings", profile_id, summary)
            tx.put("reviews", booking_id, review)
            audit(tx, "REVIEW_CREATED", "REVIEW", review["id"], user.id)
            return review

        return await self.store.run(operation)

    async def get_interviewer_rating_summary(self, interviewer_id: object) -> Document:
        binding = await self.store.reader().get("profile_keys", interviewer_id)
        profile_id = binding["profile_id"] if binding else str(interviewer_id)
        summary = await self.store.reader().get("ratings", profile_id)
        count = summary["total_reviews"] if summary else 0
        return {
            "interviewer_id": str(interviewer_id),
            "total_reviews": count,
            "average_rating": round(summary["sum"] / count, 2) if summary and count else None,
        }

    async def list_interviewer_reviews(
        self, interviewer_id: object, limit: int = 50, offset: int = 0
    ) -> list[Document]:
        binding = await self.store.reader().get("profile_keys", interviewer_id)
        profile_id = binding["profile_id"] if binding else str(interviewer_id)
        return await self.store.reader().query(
            "reviews",
            (("profile_id", "==", profile_id),),
            order="-created_at",
            limit=limit,
            offset=offset,
        )
