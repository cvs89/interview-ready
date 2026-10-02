import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import TypeAlias

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.booking import Booking, BookingStatus
from app.models.identity import InterviewerProfile, User, UserRole
from app.models.session import InterviewSession, SessionStatus

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]

FeedbackContext: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, uuid.UUID],
    dict[str, uuid.UUID],
    Settings,
]


@pytest_asyncio.fixture
async def feedback_context() -> AsyncIterator[FeedbackContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    users = {
        "admin": User(
            firebase_uid="admin_uid",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            email_verified=True,
        ),
        "interviewer": User(
            firebase_uid="interviewer_uid",
            email="interviewer@example.com",
            full_name="Interviewer One",
            role=UserRole.INTERVIEWER,
            email_verified=True,
        ),
        "other_interviewer": User(
            firebase_uid="other_interviewer_uid",
            email="other_interviewer@example.com",
            full_name="Interviewer Two",
            role=UserRole.INTERVIEWER,
            email_verified=True,
        ),
        "candidate": User(
            firebase_uid="candidate_uid",
            email="candidate@example.com",
            full_name="Candidate One",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
        "other_candidate": User(
            firebase_uid="other_candidate_uid",
            email="other_candidate@example.com",
            full_name="Candidate Two",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
    }

    user_ids: dict[str, uuid.UUID] = {}
    async with session_factory() as session:
        for user in users.values():
            session.add(user)
        await session.flush()
        for key, user in users.items():
            user_ids[key] = user.id

        profile = InterviewerProfile(
            user_id=user_ids["interviewer"],
            bio="Senior Engineer",
            title="Staff SWE",
            years_experience=10,
            default_rate_minor=15000,
            currency="USD",
            is_verified=True,
        )
        session.add(profile)

        now = datetime.now(UTC)
        slot1 = AvailabilitySlot(
            interviewer_id=user_ids["interviewer"],
            start_time=now - timedelta(hours=2),
            end_time=now - timedelta(hours=1),
            price_minor=15000,
            currency="USD",
            status=AvailabilityStatus.BOOKED,
        )
        slot2 = AvailabilitySlot(
            interviewer_id=user_ids["interviewer"],
            start_time=now + timedelta(hours=1),
            end_time=now + timedelta(hours=2),
            price_minor=15000,
            currency="USD",
            status=AvailabilityStatus.BOOKED,
        )
        session.add_all([slot1, slot2])
        await session.flush()

        booking_confirmed = Booking(
            slot_id=slot1.id,
            candidate_id=user_ids["candidate"],
            interviewer_id=user_ids["interviewer"],
            status=BookingStatus.CONFIRMED,
            price_minor=15000,
            currency="USD",
            confirmed_at=now - timedelta(days=1),
        )
        session.add(booking_confirmed)
        await session.flush()

        interview_session = InterviewSession(
            id=uuid.uuid4(),
            booking_id=booking_confirmed.id,
            livekit_room_name="room_test_123",
            status=SessionStatus.ACTIVE,
            started_at=now - timedelta(hours=2),
        )
        session.add(interview_session)

        booking_ids: dict[str, uuid.UUID] = {
            "booking_confirmed": booking_confirmed.id,
        }
        await session.commit()

    settings = Settings(
        app_name="Interview Ready API Test",
        database_url="sqlite+aiosqlite:///:memory:",
        auth_disabled=True,
        jwt_signing_key="test_secret_key_long_enough_for_sha256",
        livekit_api_key="test_livekit_key",
        livekit_api_secret="test_livekit_secret_at_least_32_characters",
        livekit_url="wss://livekit.example.com",
    )

    current_user_override = users["interviewer"]

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def override_get_current_user() -> User:
        return current_user_override

    app = create_app(settings)
    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

        def set_user(user_key: str) -> None:
            nonlocal current_user_override
            current_user_override = users[user_key]

        client.set_user = set_user  # type: ignore[attr-defined]
        yield client, session_factory, user_ids, booking_ids, settings

    await engine.dispose()


@pytest.mark.asyncio
async def test_rubric_draft_save_and_retrieve(feedback_context: FeedbackContext) -> None:
    client, _, _, booking_ids, _ = feedback_context
    client.set_user("interviewer")  # type: ignore[attr-defined]
    booking_id = booking_ids["booking_confirmed"]

    # 1. Save draft
    draft_payload = {
        "technical_score": 4,
        "problem_solving_score": 5,
        "communication_score": 3,
        "detailed_feedback": "Great algorithmic problem solving.",
        "action_items": "Practice distributed systems trade-offs.",
        "private_interviewer_notes": "Candidate hesitated on cache invalidation.",
    }
    resp = await client.post(f"/api/v1/bookings/{booking_id}/rubric/draft", json=draft_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["booking_id"] == str(booking_id)
    assert data["technical_score"] == 4
    assert data["problem_solving_score"] == 5
    assert data["communication_score"] == 3
    assert data["status"] == "DRAFT"
    assert data["version"] == 1
    assert data["private_interviewer_notes"] == "Candidate hesitated on cache invalidation."

    # 2. Get interviewer rubric
    get_resp = await client.get(f"/api/v1/bookings/{booking_id}/rubric")
    assert get_resp.status_code == 200
    assert get_resp.json()["private_interviewer_notes"] == (
        "Candidate hesitated on cache invalidation."
    )

    # 3. Update draft
    update_payload = {
        "technical_score": 5,
    }
    update_resp = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft", json=update_payload
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["technical_score"] == 5
    assert update_resp.json()["version"] == 2


@pytest.mark.asyncio
async def test_wrong_interviewer_cannot_edit_rubric(feedback_context: FeedbackContext) -> None:
    client, _, _, booking_ids, _ = feedback_context
    client.set_user("other_interviewer")  # type: ignore[attr-defined]
    booking_id = booking_ids["booking_confirmed"]

    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft",
        json={"technical_score": 3},
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_score_range_validation(feedback_context: FeedbackContext) -> None:
    client, _, _, booking_ids, _ = feedback_context
    client.set_user("interviewer")  # type: ignore[attr-defined]
    booking_id = booking_ids["booking_confirmed"]

    # Draft with score > 5
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft",
        json={"technical_score": 6},
    )
    assert resp.status_code == 422

    # Draft with score < 1
    resp = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft",
        json={"technical_score": 0},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_candidate_cannot_view_draft_or_notes(feedback_context: FeedbackContext) -> None:
    client, _, _, booking_ids, _ = feedback_context
    booking_id = booking_ids["booking_confirmed"]

    # Interviewer creates draft with private notes
    client.set_user("interviewer")  # type: ignore[attr-defined]
    await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft",
        json={
            "technical_score": 4,
            "private_interviewer_notes": "CONFIDENTIAL INTERVIEWER NOTE",
        },
    )

    # Candidate tries to access interviewer rubric view -> 403
    client.set_user("candidate")  # type: ignore[attr-defined]
    resp = await client.get(f"/api/v1/bookings/{booking_id}/rubric")
    assert resp.status_code == 403

    # Candidate tries to get feedback before submission -> 404
    resp = await client.get(f"/api/v1/bookings/{booking_id}/feedback")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "FEEDBACK_NOT_READY"


@pytest.mark.asyncio
async def test_rubric_submission_completes_booking_and_locks(
    feedback_context: FeedbackContext,
) -> None:
    client, session_factory, _, booking_ids, _ = feedback_context
    booking_id = booking_ids["booking_confirmed"]

    # Interviewer submits rubric
    client.set_user("interviewer")  # type: ignore[attr-defined]
    submit_payload = {
        "technical_score": 4,
        "problem_solving_score": 5,
        "communication_score": 4,
        "detailed_feedback": "Excellent performance on graph algorithms and system scaling.",
        "action_items": "Brush up on concurrency primitives.",
        "private_interviewer_notes": "Strong candidate for hire.",
    }
    resp = await client.post(f"/api/v1/bookings/{booking_id}/rubric/submit", json=submit_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUBMITTED"
    assert data["submitted_at"] is not None

    # Verify DB state: booking is COMPLETED and session is ENDED
    async with session_factory() as session:
        booking = (
            await session.execute(select(Booking).where(Booking.id == booking_id))
        ).scalar_one()
        assert booking.status == BookingStatus.COMPLETED
        assert booking.completed_at is not None

        sess = (
            await session.execute(
                select(InterviewSession).where(InterviewSession.booking_id == booking_id)
            )
        ).scalar_one()
        assert sess.status == SessionStatus.ENDED
        assert sess.ended_at is not None

    # Attempting to edit or re-submit rubric returns error
    resp_draft = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/draft",
        json={"technical_score": 3},
    )
    assert resp_draft.status_code == 400
    assert resp_draft.json()["error"]["code"] == "RUBRIC_LOCKED"

    resp_submit = await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/submit",
        json=submit_payload,
    )
    assert resp_submit.status_code == 400
    assert resp_submit.json()["error"]["code"] == "RUBRIC_ALREADY_SUBMITTED"

    # Candidate accesses feedback: CANNOT see private_interviewer_notes
    client.set_user("candidate")  # type: ignore[attr-defined]
    candidate_resp = await client.get(f"/api/v1/bookings/{booking_id}/feedback")
    assert candidate_resp.status_code == 200
    c_data = candidate_resp.json()
    assert "private_interviewer_notes" not in c_data
    assert c_data["technical_score"] == 4
    assert c_data["problem_solving_score"] == 5
    assert c_data["detailed_feedback"] == (
        "Excellent performance on graph algorithms and system scaling."
    )


@pytest.mark.asyncio
async def test_reviews_lifecycle(feedback_context: FeedbackContext) -> None:
    client, _, user_ids, booking_ids, _ = feedback_context
    booking_id = booking_ids["booking_confirmed"]
    interviewer_id = user_ids["interviewer"]

    # 1. Candidate tries to review booking before completion -> rejected 400
    client.set_user("candidate")  # type: ignore[attr-defined]
    review_payload = {
        "rating": 5,
        "review": "Fantastic interviewer, very supportive and clear.",
    }
    resp = await client.post(f"/api/v1/bookings/{booking_id}/review", json=review_payload)
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "BOOKING_NOT_COMPLETED"

    # Complete the interview via rubric submission
    client.set_user("interviewer")  # type: ignore[attr-defined]
    await client.post(
        f"/api/v1/bookings/{booking_id}/rubric/submit",
        json={
            "technical_score": 5,
            "problem_solving_score": 5,
            "communication_score": 5,
            "detailed_feedback": "Flawless session.",
        },
    )

    # 2. Other candidate tries to review -> 403 Forbidden
    client.set_user("other_candidate")  # type: ignore[attr-defined]
    resp_other = await client.post(f"/api/v1/bookings/{booking_id}/review", json=review_payload)
    assert resp_other.status_code == 403

    # 3. Invalid rating constraints
    client.set_user("candidate")  # type: ignore[attr-defined]
    resp_invalid_high = await client.post(
        f"/api/v1/bookings/{booking_id}/review", json={"rating": 6}
    )
    assert resp_invalid_high.status_code == 422
    resp_invalid_low = await client.post(
        f"/api/v1/bookings/{booking_id}/review", json={"rating": 0}
    )
    assert resp_invalid_low.status_code == 422

    # 4. Valid review submission
    resp_ok = await client.post(f"/api/v1/bookings/{booking_id}/review", json=review_payload)
    assert resp_ok.status_code == 201
    review_data = resp_ok.json()
    assert review_data["rating"] == 5
    assert review_data["review"] == "Fantastic interviewer, very supportive and clear."

    # 5. Duplicate review is rejected with 409
    resp_dup = await client.post(f"/api/v1/bookings/{booking_id}/review", json=review_payload)
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"

    # 6. Public rating summary and review listings
    summary_resp = await client.get(f"/api/v1/interviewers/{interviewer_id}/rating")
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["average_rating"] == 5.0
    assert summary_data["total_reviews"] == 1

    list_resp = await client.get(f"/api/v1/interviewers/{interviewer_id}/reviews")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["rating"] == 5
