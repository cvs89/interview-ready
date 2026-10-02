import time
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated, TypeAlias

import httpx
import jwt
import pytest
import pytest_asyncio
from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_session
from app.integrations.redis import get_redis
from app.main import create_app
from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.booking import Booking, BookingStatus
from app.models.identity import InterviewerProfile, User, UserRole
from app.models.session import InterviewSession, SessionStatus

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]


class MockRedis:
    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float | None]] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        expiry = time.time() + ex if ex else None
        self._data[key] = (value, expiry)

    async def get(self, key: str) -> str | None:
        if key not in self._data:
            return None
        val, expiry = self._data[key]
        if expiry is not None and time.time() > expiry:
            del self._data[key]
            return None
        return val

    async def getdel(self, key: str) -> str | None:
        val = await self.get(key)
        if key in self._data:
            del self._data[key]
        return val

    async def delete(self, *keys: str) -> int:
        count = 0
        for k in keys:
            if k in self._data:
                del self._data[k]
                count += 1
        return count

    async def eval(self, script: str, numkeys: int, *keys_and_args: str) -> str | None:
        key = keys_and_args[0]
        return await self.getdel(key)

    async def aclose(self) -> None:
        self._data.clear()


DesktopAuthContext: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, uuid.UUID],
    dict[str, uuid.UUID],
    MockRedis,
    Settings,
]


@pytest_asyncio.fixture
async def desktop_auth_context() -> AsyncIterator[DesktopAuthContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    mock_redis = MockRedis()

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
        "other_user": User(
            firebase_uid="other_user_uid",
            email="other@example.com",
            full_name="Other Candidate",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
    }

    async with session_factory() as session:
        session.add_all(users.values())
        await session.flush()

        profile = InterviewerProfile(
            user_id=users["interviewer"].id,
            bio="Senior Staff Engineer",
            title="Tech Lead",
            years_experience=8,
            default_rate_minor=10_000,
            currency="INR",
            is_verified=True,
        )
        session.add(profile)
        await session.commit()
        ids = {name: user.id for name, user in users.items()}
        ids["profile_id"] = profile.id

    current = {"user_id": ids["candidate"]}
    settings = Settings(
        app_env="test",
        desktop_ticket_ttl_seconds=60,
        join_window_lead_minutes=10,
        join_window_grace_minutes=30,
        session_jwt_secret="custom_test_session_jwt_secret_98765",
        session_jwt_ttl_seconds=3600,
        livekit_url="wss://livekit.interviewready.test",
        livekit_api_key="test_livekit_key",
        livekit_api_secret="test_livekit_secret_that_is_at_least_32_bytes_long",
        livekit_token_ttl_seconds=3600,
    )
    app = create_app(settings)

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def override_current_user(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> User:
        user = await session.get(User, current["user_id"])
        assert user is not None
        return user

    def override_redis() -> Redis:
        return mock_redis  # type: ignore[return-value]

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_redis] = override_redis

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, current, ids, mock_redis, settings
    await engine.dispose()


async def create_booking_in_db(
    session_factory: SessionFactory,
    profile_id: uuid.UUID,
    candidate_id: uuid.UUID,
    interviewer_id: uuid.UUID,
    *,
    start_offset_minutes: int = 0,
    duration_minutes: int = 60,
    status: BookingStatus = BookingStatus.CONFIRMED,
) -> Booking:
    now = datetime.now(UTC)
    start_time = now + timedelta(minutes=start_offset_minutes)
    end_time = start_time + timedelta(minutes=duration_minutes)

    async with session_factory() as session:
        slot = AvailabilitySlot(
            interviewer_id=profile_id,
            start_time=start_time,
            end_time=end_time,
            price_minor=10_000,
            currency="INR",
            status=AvailabilityStatus.BOOKED,
        )
        session.add(slot)
        await session.flush()

        booking = Booking(
            slot_id=slot.id,
            candidate_id=candidate_id,
            interviewer_id=interviewer_id,
            status=status,
            price_minor=10_000,
            currency="INR",
            confirmed_at=now if status == BookingStatus.CONFIRMED else None,
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking


@pytest.mark.asyncio
async def test_mint_and_exchange_desktop_ticket_flow(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, redis, settings = desktop_auth_context
    booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=5,  # Within 10-min lead join window
    )

    # Candidate mints ticket
    current["user_id"] = ids["candidate"]
    mint_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    assert mint_res.status_code == 201, mint_res.text
    mint_data = mint_res.json()
    ticket = mint_data["ticket"]
    assert len(ticket) >= 32
    assert mint_data["expires_in_seconds"] == 60
    assert mint_data["booking_id"] == str(booking.id)

    # Candidate exchanges ticket
    exchange_res = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": ticket, "booking_id": str(booking.id)},
    )
    assert exchange_res.status_code == 200, exchange_res.text
    exchange_data = exchange_res.json()

    assert exchange_data["booking_id"] == str(booking.id)
    assert exchange_data["role"] == "CANDIDATE"
    assert exchange_data["livekit_url"] == settings.livekit_url
    assert exchange_data["room_name"].startswith("room_")

    # Verify session JWT structure and claims
    session_jwt = exchange_data["session_jwt"]
    decoded_jwt = jwt.decode(session_jwt, settings.session_jwt_secret, algorithms=["HS256"])
    assert decoded_jwt["sub"] == str(ids["candidate"])
    assert decoded_jwt["booking_id"] == str(booking.id)
    assert decoded_jwt["role"] == "CANDIDATE"
    assert "jti" in decoded_jwt

    # Verify LiveKit token structure and video grant
    livekit_token = exchange_data["livekit_token"]
    decoded_livekit = jwt.decode(livekit_token, settings.livekit_api_secret, algorithms=["HS256"])
    assert decoded_livekit["sub"] == str(ids["candidate"])
    assert decoded_livekit["video"]["room"] == exchange_data["room_name"]
    assert decoded_livekit["video"]["roomJoin"] is True
    assert decoded_livekit["video"]["canPublish"] is True


@pytest.mark.asyncio
async def test_ticket_is_strictly_one_time_use(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context
    booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=0,
    )

    current["user_id"] = ids["candidate"]
    mint_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    ticket = mint_res.json()["ticket"]

    # First exchange succeeds
    res1 = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": ticket},
    )
    assert res1.status_code == 200

    # Immediate replay / second exchange MUST fail (401)
    res2 = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": ticket},
    )
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "INVALID_OR_EXPIRED_TICKET"


@pytest.mark.asyncio
async def test_wrong_user_cannot_mint_ticket(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context
    booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=0,
    )

    # Other user attempts to mint ticket for this booking
    current["user_id"] = ids["other_user"]
    mint_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    assert mint_res.status_code == 403
    assert mint_res.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_cross_check_booking_id_mismatch_fails(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context
    booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=0,
    )

    current["user_id"] = ids["candidate"]
    mint_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    ticket = mint_res.json()["ticket"]

    # Exchange with a mismatched booking_id
    exchange_res = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": ticket, "booking_id": str(uuid.uuid4())},
    )
    assert exchange_res.status_code == 400
    assert exchange_res.json()["error"]["code"] == "BOOKING_MISMATCH"


@pytest.mark.asyncio
async def test_cancelled_or_unconfirmed_booking_cannot_join(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context
    cancelled_booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=0,
        status=BookingStatus.CANCELLED,
    )

    current["user_id"] = ids["candidate"]
    res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(cancelled_booking.id)},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "BOOKING_NOT_JOINABLE"


@pytest.mark.asyncio
async def test_join_window_lead_and_grace_enforcement(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context

    # 1. Booking far in the future (> 10 mins before start)
    future_booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=120,  # 2 hours away
    )

    current["user_id"] = ids["candidate"]
    future_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(future_booking.id)},
    )
    assert future_res.status_code == 400
    assert future_res.json()["error"]["code"] == "JOIN_WINDOW_NOT_STARTED"

    # Join status should indicate JOIN_WINDOW_NOT_STARTED
    status_res = await client.get(f"/api/v1/bookings/{future_booking.id}/join-status")
    assert status_res.status_code == 200
    assert status_res.json()["can_join"] is False
    assert status_res.json()["reason"] == "JOIN_WINDOW_NOT_STARTED"

    # 2. Booking long in the past (> 30 mins after end)
    past_booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=-120,
        duration_minutes=60,  # Ended 60 mins ago (> 30 min grace period)
    )

    past_res = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(past_booking.id)},
    )
    assert past_res.status_code == 400
    assert past_res.json()["error"]["code"] == "JOIN_WINDOW_CLOSED"


@pytest.mark.asyncio
async def test_both_participants_joining_promotes_session_to_active(
    desktop_auth_context: DesktopAuthContext,
) -> None:
    client, session_factory, current, ids, _, _ = desktop_auth_context
    booking = await create_booking_in_db(
        session_factory,
        ids["profile_id"],
        ids["candidate"],
        ids["interviewer"],
        start_offset_minutes=0,
    )

    # 1. Candidate mints and exchanges
    current["user_id"] = ids["candidate"]
    c_mint = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    c_exchange = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": c_mint.json()["ticket"]},
    )
    assert c_exchange.status_code == 200
    room_name = c_exchange.json()["room_name"]

    async with session_factory() as session:
        interview_session = (
            await session.execute(
                select(InterviewSession).where(InterviewSession.booking_id == booking.id)
            )
        ).scalar_one_or_none()
        assert interview_session is not None
        assert interview_session.status == SessionStatus.READY
        assert interview_session.candidate_joined_at is not None
        assert interview_session.interviewer_joined_at is None

    # 2. Interviewer mints and exchanges
    current["user_id"] = ids["interviewer"]
    i_mint = await client.post(
        "/api/v1/auth/mint-desktop-ticket",
        json={"booking_id": str(booking.id)},
    )
    i_exchange = await client.post(
        "/api/v1/auth/exchange-desktop-ticket",
        json={"ticket": i_mint.json()["ticket"]},
    )
    assert i_exchange.status_code == 200
    assert i_exchange.json()["room_name"] == room_name

    # Check that session is now ACTIVE and booking is IN_PROGRESS
    async with session_factory() as session:
        interview_session = (
            await session.execute(
                select(InterviewSession).where(InterviewSession.booking_id == booking.id)
            )
        ).scalar_one_or_none()
        assert interview_session is not None
        assert interview_session.status == SessionStatus.ACTIVE
        assert interview_session.candidate_joined_at is not None
        assert interview_session.interviewer_joined_at is not None
        assert interview_session.started_at is not None

        db_booking = await session.get(Booking, booking.id)
        assert db_booking is not None
        assert db_booking.status == BookingStatus.IN_PROGRESS
        assert db_booking.started_at is not None
