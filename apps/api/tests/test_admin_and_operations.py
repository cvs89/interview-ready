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
from app.models.audit import AuditLog
from app.models.availability import (
    AvailabilitySlot,
    AvailabilityStatus,
    InterviewerVerification,
    VerificationStatus,
)
from app.models.booking import Booking, BookingStatus, Payment, PaymentStatus
from app.models.identity import InterviewerProfile, User, UserRole, UserStatus

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]

AdminContext: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, User],
    dict[str, uuid.UUID],
]


@pytest_asyncio.fixture
async def admin_context() -> AsyncIterator[AdminContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    admin_id = uuid.uuid4()
    interviewer_id = uuid.uuid4()
    candidate_id = uuid.uuid4()

    admin_user = User(
        id=admin_id,
        firebase_uid="admin_uid",
        email="admin@example.com",
        full_name="Admin User",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    interviewer_user = User(
        id=interviewer_id,
        firebase_uid="interviewer_uid",
        email="interviewer@example.com",
        full_name="Senior Engineer",
        role=UserRole.INTERVIEWER,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )
    candidate_user = User(
        id=candidate_id,
        firebase_uid="candidate_uid",
        email="candidate@example.com",
        full_name="Job Candidate",
        role=UserRole.CANDIDATE,
        status=UserStatus.ACTIVE,
        email_verified=True,
    )

    interviewer_profile = InterviewerProfile(
        id=interviewer_id,
        user_id=interviewer_id,
        title="Staff Engineer",
        years_experience=8,
        default_rate_minor=10000,
        currency="USD",
        is_verified=True,
    )

    slot_id = uuid.uuid4()
    booking_id = uuid.uuid4()
    payment_id = uuid.uuid4()
    verification_id = uuid.uuid4()

    now = datetime.now(UTC)
    slot = AvailabilitySlot(
        id=slot_id,
        interviewer_id=interviewer_id,
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=1),
        price_minor=10000,
        currency="USD",
        status=AvailabilityStatus.BOOKED,
    )

    booking = Booking(
        id=booking_id,
        slot_id=slot_id,
        candidate_id=candidate_id,
        interviewer_id=interviewer_id,
        status=BookingStatus.CONFIRMED,
        price_minor=10000,
        currency="USD",
        confirmed_at=now,
    )

    payment = Payment(
        id=payment_id,
        booking_id=booking_id,
        candidate_id=candidate_id,
        amount_minor=10000,
        currency="USD",
        provider="stripe",
        status=PaymentStatus.PAID,
        provider_payment_id="pi_test_12345",
    )

    verification = InterviewerVerification(
        id=verification_id,
        interviewer_id=interviewer_id,
        status=VerificationStatus.APPROVED,
        submitted_at=now - timedelta(days=5),
        reviewed_at=now - timedelta(days=4),
        reviewed_by=admin_id,
    )

    async with session_factory() as session:
        session.add_all(
            [
                admin_user,
                interviewer_user,
                candidate_user,
                interviewer_profile,
                slot,
                booking,
                payment,
                verification,
            ]
        )
        await session.commit()
        await session.refresh(admin_user)
        await session.refresh(interviewer_user)
        await session.refresh(candidate_user)
        await session.refresh(interviewer_profile)
        await session.refresh(slot)
        await session.refresh(booking)
        await session.refresh(payment)
        await session.refresh(verification)

    users_map = {
        "admin": admin_user,
        "interviewer": interviewer_user,
        "candidate": candidate_user,
    }
    resources_map = {
        "interviewer_profile_id": interviewer_profile.id,
        "slot_id": slot.id,
        "booking_id": booking.id,
        "payment_id": payment.id,
        "verification_id": verification.id,
    }

    current_user_override = admin_user

    async def override_get_current_user() -> User:
        return current_user_override

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    settings = Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        auth_mode="firebase",
        log_level="INFO",
    )
    app = create_app(settings=settings)
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_session] = override_get_session

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:

        def set_user(user_key: str) -> None:
            nonlocal current_user_override
            current_user_override = users_map[user_key]

        client.set_user = set_user  # type: ignore[attr-defined]
        yield client, session_factory, users_map, resources_map

    await engine.dispose()


@pytest.mark.asyncio
async def test_non_admin_denied_access(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context

    # Set non-admin candidate
    client.set_user("candidate")  # type: ignore[attr-defined]

    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/admin/verifications")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/admin/bookings")
    assert resp.status_code == 403

    resp = await client.get("/api/v1/admin/payments")
    assert resp.status_code == 403

    resp = await client.patch(
        f"/api/v1/admin/users/{users['candidate'].id}/status",
        json={"status": "SUSPENDED", "reason": "abusive"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users_and_filters(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context

    client.set_user("admin")  # type: ignore[attr-defined]

    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3

    # Search by query
    resp = await client.get("/api/v1/admin/users?search=Senior")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "interviewer@example.com"

    # Filter by role
    resp = await client.get("/api/v1/admin/users?role=CANDIDATE")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["role"] == "CANDIDATE"

    # Filter by status
    resp = await client.get("/api/v1/admin/users?status=ACTIVE")
    assert resp.status_code == 200
    assert resp.json()["total"] == 3


@pytest.mark.asyncio
async def test_admin_user_status_update_and_audit(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context
    candidate = users["candidate"]

    client.set_user("admin")  # type: ignore[attr-defined]

    # Admin updates candidate status to SUSPENDED
    resp = await client.patch(
        f"/api/v1/admin/users/{candidate.id}/status",
        json={"status": "SUSPENDED", "reason": "Violation of terms"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUSPENDED"

    # Check audit log was written
    async with session_factory() as session:
        result = await session.execute(
            select(AuditLog).where(
                AuditLog.event_type == "ADMIN_USER_STATUS_UPDATED",
                AuditLog.resource_id == str(candidate.id),
            )
        )
        audit_log = result.scalar_one_or_none()
        assert audit_log is not None
        assert audit_log.actor_user_id == users["admin"].id
        assert audit_log.metadata_json["old_status"] == "ACTIVE"
        assert audit_log.metadata_json["new_status"] == "SUSPENDED"
        assert audit_log.metadata_json["reason"] == "Violation of terms"


@pytest.mark.asyncio
async def test_admin_cannot_disable_self(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context
    admin = users["admin"]

    client.set_user("admin")  # type: ignore[attr-defined]

    resp = await client.patch(
        f"/api/v1/admin/users/{admin.id}/status",
        json={"status": "DISABLED", "reason": "Accidental self disable"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CANNOT_DISABLE_SELF"


@pytest.mark.asyncio
async def test_suspended_user_cannot_authenticate(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context
    candidate = users["candidate"]

    from app.services.identity import IdentityService

    # Update candidate to SUSPENDED in DB
    async with session_factory() as session:
        loaded = await session.get(User, candidate.id)
        assert loaded is not None
        loaded.status = UserStatus.SUSPENDED
        await session.commit()

    # Now attempt authenticate via claims
    async with session_factory() as session:
        service = IdentityService(session)
        with pytest.raises(Exception) as exc_info:
            await service.authenticate(
                {
                    "uid": candidate.firebase_uid,
                    "email": candidate.email,
                    "name": candidate.full_name,
                    "email_verified": True,
                }
            )
        assert "ACCOUNT_SUSPENDED" in str(exc_info.value)


@pytest.mark.asyncio
async def test_admin_verification_queue_and_review(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context

    client.set_user("admin")  # type: ignore[attr-defined]

    # List verifications
    resp = await client.get("/api/v1/admin/verifications")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "APPROVED"
    assert data["items"][0]["email"] == "interviewer@example.com"

    # Review verification
    resp = await client.patch(
        f"/api/v1/admin/interviewer-verifications/{resources['interviewer_profile_id']}",
        json={"status": "REJECTED", "notes": "Missing portfolio documentation"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_admin_inspect_bookings_and_payments(admin_context: AdminContext) -> None:
    client, session_factory, users, resources = admin_context

    client.set_user("admin")  # type: ignore[attr-defined]

    # Inspect bookings
    resp = await client.get("/api/v1/admin/bookings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    booking = data["items"][0]
    assert booking["status"] == "CONFIRMED"
    assert booking["candidate_name"] == "Job Candidate"
    assert booking["interviewer_name"] == "Senior Engineer"
    assert booking["payment_status"] == "PAID"

    # Inspect single booking
    resp = await client.get(f"/api/v1/admin/bookings/{resources['booking_id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(resources["booking_id"])

    # Inspect payments
    resp = await client.get("/api/v1/admin/payments")
    assert resp.status_code == 200
    pdata = resp.json()
    assert pdata["total"] == 1
    payment = pdata["items"][0]
    assert payment["amount_minor"] == 10000
    assert payment["status"] == "PAID"
    assert payment["provider_payment_id"] == "pi_test_12345"

    # Verify no sensitive keys leaked
    raw_text = resp.text
    assert "secret" not in raw_text.lower()
    assert "livekit_token" not in raw_text.lower()
    assert "ticket_token" not in raw_text.lower()
