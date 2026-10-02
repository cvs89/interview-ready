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
from app.integrations.notifications import MockEmailNotificationChannel, MockFCMNotificationChannel
from app.main import create_app
from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.booking import Booking, BookingStatus
from app.models.identity import InterviewerProfile, User, UserRole
from app.services.audit import sanitize_metadata
from app.services.notification import NotificationService

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]

Module10Context: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, uuid.UUID],
    dict[str, uuid.UUID],
    Settings,
]


@pytest_asyncio.fixture
async def module10_context() -> AsyncIterator[Module10Context]:
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
        "candidate": User(
            firebase_uid="candidate_uid",
            email="candidate@example.com",
            full_name="Candidate One",
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
            bio="Senior Staff Engineer",
            title="Principal SWE",
            years_experience=12,
            default_rate_minor=20000,
            currency="USD",
            is_verified=True,
        )
        session.add(profile)

        now = datetime.now(UTC)
        slot1 = AvailabilitySlot(
            interviewer_id=user_ids["interviewer"],
            start_time=now + timedelta(hours=24),
            end_time=now + timedelta(hours=25),
            price_minor=20000,
            currency="USD",
            status=AvailabilityStatus.BOOKED,
        )
        slot_expired = AvailabilitySlot(
            interviewer_id=user_ids["interviewer"],
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=1),
            price_minor=20000,
            currency="USD",
            status=AvailabilityStatus.RESERVED,
            reserved_by=user_ids["candidate"],
            reservation_expires_at=now - timedelta(minutes=5),
        )
        session.add_all([slot1, slot_expired])
        await session.flush()

        booking_confirmed = Booking(
            slot_id=slot1.id,
            candidate_id=user_ids["candidate"],
            interviewer_id=user_ids["interviewer"],
            status=BookingStatus.CONFIRMED,
            price_minor=20000,
            currency="USD",
            confirmed_at=now,
        )
        booking_expired = Booking(
            slot_id=slot_expired.id,
            candidate_id=user_ids["candidate"],
            interviewer_id=user_ids["interviewer"],
            status=BookingStatus.PENDING_PAYMENT,
            price_minor=20000,
            currency="USD",
        )
        session.add_all([booking_confirmed, booking_expired])
        await session.flush()

        booking_ids: dict[str, uuid.UUID] = {
            "booking_confirmed": booking_confirmed.id,
            "booking_expired": booking_expired.id,
            "slot1": slot1.id,
            "slot_expired": slot_expired.id,
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

    current_user_override = users["candidate"]

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
async def test_notification_dispatch_and_deduplication(module10_context: Module10Context) -> None:
    _, session_factory, user_ids, booking_ids, _ = module10_context
    candidate_id = user_ids["candidate"]
    booking_id = booking_ids["booking_confirmed"]

    email_channel = MockEmailNotificationChannel()
    fcm_channel = MockFCMNotificationChannel()

    async with session_factory() as session:
        candidate = (
            await session.execute(select(User).where(User.id == candidate_id))
        ).scalar_one()
        service = NotificationService(
            session=session,
            email_channel=email_channel,
            fcm_channel=fcm_channel,
        )

        # 1. First dispatch -> SENT across EMAIL, FCM, and IN_APP
        results = await service.dispatch_event(
            event_type="BOOKING_CONFIRMED",
            recipient=candidate,
            title="Interview Booked",
            body="Your interview is confirmed.",
            data={"booking_id": str(booking_id)},
            reference_id=str(booking_id),
            channels=["EMAIL", "FCM", "IN_APP"],
        )
        assert results["EMAIL"] == "SENT"
        assert results["FCM"] == "SENT"
        assert results["IN_APP"] == "SENT"
        assert len(email_channel.sent_messages) == 1
        assert len(fcm_channel.sent_messages) == 1

        # 2. Second dispatch with identical idempotency key -> DEDUPLICATED
        results2 = await service.dispatch_event(
            event_type="BOOKING_CONFIRMED",
            recipient=candidate,
            title="Interview Booked",
            body="Your interview is confirmed.",
            data={"booking_id": str(booking_id)},
            reference_id=str(booking_id),
            channels=["EMAIL", "FCM", "IN_APP"],
        )
        assert results2["EMAIL"] == "DEDUPLICATED"
        assert results2["FCM"] == "DEDUPLICATED"
        assert results2["IN_APP"] == "DEDUPLICATED"
        assert len(email_channel.sent_messages) == 1
        assert len(fcm_channel.sent_messages) == 1


@pytest.mark.asyncio
async def test_in_app_notification_api_endpoints(module10_context: Module10Context) -> None:
    client, session_factory, user_ids, booking_ids, _ = module10_context
    candidate_id = user_ids["candidate"]
    booking_id = booking_ids["booking_confirmed"]

    # Seed 2 in-app notifications
    async with session_factory() as session:
        candidate = (
            await session.execute(select(User).where(User.id == candidate_id))
        ).scalar_one()
        service = NotificationService(session=session)
        await service.dispatch_event(
            event_type="REMINDER_24H",
            recipient=candidate,
            title="Reminder 24h",
            body="Interview starts in 24 hours.",
            data={"booking_id": str(booking_id)},
            reference_id=str(booking_id),
            channels=["IN_APP"],
        )
        await service.dispatch_event(
            event_type="REMINDER_1H",
            recipient=candidate,
            title="Reminder 1h",
            body="Interview starts in 1 hour.",
            data={"booking_id": str(booking_id)},
            reference_id=f"{booking_id}_1h",
            channels=["IN_APP"],
        )

    client.set_user("candidate")  # type: ignore[attr-defined]

    # List notifications
    resp = await client.get("/api/v1/notifications/me")
    assert resp.status_code == 200
    notifications = resp.json()
    assert len(notifications) == 2
    assert all(n["read_at"] is None for n in notifications)

    # Mark first notification as read
    notif_id = notifications[0]["id"]
    mark_resp = await client.patch(f"/api/v1/notifications/{notif_id}/read")
    assert mark_resp.status_code == 200
    assert mark_resp.json()["success"] is True

    # Filter unread notifications -> 1 remaining
    unread_resp = await client.get("/api/v1/notifications/me?unread_only=true")
    assert unread_resp.status_code == 200
    assert len(unread_resp.json()) == 1

    # Mark all read
    read_all_resp = await client.post("/api/v1/notifications/read-all")
    assert read_all_resp.status_code == 200
    assert read_all_resp.json()["marked_count"] >= 1

    unread_resp_after = await client.get("/api/v1/notifications/me?unread_only=true")
    assert unread_resp_after.status_code == 200
    assert len(unread_resp_after.json()) == 0


@pytest.mark.asyncio
async def test_task_service_and_reservation_expiry_idempotence(
    module10_context: Module10Context,
) -> None:
    client, session_factory, _, booking_ids, _ = module10_context
    expired_booking_id = booking_ids["booking_expired"]
    expired_slot_id = booking_ids["slot_expired"]

    # 1. Run expire_reservations task via internal task processor
    resp = await client.post(
        "/api/v1/internal/tasks/process",
        json={"task_type": "expire_reservations", "payload": {}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_type"] == "expire_reservations"
    assert data["processed_count"] == 1

    # Verify slot is AVAILABLE and booking is EXPIRED
    async with session_factory() as session:
        slot = (
            await session.execute(
                select(AvailabilitySlot).where(AvailabilitySlot.id == expired_slot_id)
            )
        ).scalar_one()
        assert slot.status == AvailabilityStatus.AVAILABLE
        assert slot.reserved_by is None

        booking = (
            await session.execute(select(Booking).where(Booking.id == expired_booking_id))
        ).scalar_one()
        assert booking.status == BookingStatus.EXPIRED

    # 2. Run expire_reservations task again -> idempotent (count == 0)
    resp2 = await client.post(
        "/api/v1/internal/tasks/process",
        json={"task_type": "expire_reservations", "payload": {}},
    )
    assert resp2.status_code == 200
    assert resp2.json()["processed_count"] == 0


@pytest.mark.asyncio
async def test_reminder_task_scanning_and_dispatch(module10_context: Module10Context) -> None:
    client, _, _, _, _ = module10_context

    resp = await client.post(
        "/api/v1/internal/tasks/process",
        json={"task_type": "send_reminders", "payload": {}},
    )
    assert resp.status_code == 200
    assert resp.json()["task_type"] == "send_reminders"


@pytest.mark.asyncio
async def test_audit_logs_emitted_and_queried(module10_context: Module10Context) -> None:
    client, _, _, _, _ = module10_context

    # 1. Non-admin accessing audit logs -> 403 Forbidden
    client.set_user("candidate")  # type: ignore[attr-defined]
    forbidden_resp = await client.get("/api/v1/admin/audit-logs")
    assert forbidden_resp.status_code == 403

    # 2. Admin querying audit logs
    client.set_user("admin")  # type: ignore[attr-defined]
    resp = await client.get("/api/v1/admin/audit-logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert isinstance(logs, list)


def test_sensitive_metadata_sanitization() -> None:
    raw = {
        "booking_id": "123",
        "secret": "super_secret_token",
        "access_token": "bearer_abc",
        "nested": {
            "password": "plain_password",
            "safe_field": 42,
        },
    }
    sanitized = sanitize_metadata(raw)
    assert sanitized["booking_id"] == "123"
    assert sanitized["secret"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["nested"]["password"] == "[REDACTED]"
    assert sanitized["nested"]["safe_field"] == 42
