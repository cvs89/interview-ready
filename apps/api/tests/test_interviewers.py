import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, TypeAlias

import httpx
import pytest
import pytest_asyncio
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_session
from app.main import create_app
from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.identity import User, UserRole

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]
MarketplaceContext: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, uuid.UUID],
    dict[str, uuid.UUID],
]


@pytest_asyncio.fixture
async def marketplace_context() -> AsyncIterator[MarketplaceContext]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    users = {
        "admin": User(
            firebase_uid="admin",
            email="admin@example.com",
            full_name="Admin User",
            role=UserRole.ADMIN,
            email_verified=True,
        ),
        "first": User(
            firebase_uid="first",
            email="first@example.com",
            full_name="First Interviewer",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
        "second": User(
            firebase_uid="second",
            email="second@example.com",
            full_name="Second Interviewer",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
    }
    async with session_factory() as session:
        session.add_all(users.values())
        await session.commit()
        ids = {name: user.id for name, user in users.items()}

    current = {"user_id": ids["first"]}
    app = create_app(Settings(app_env="test"))

    async def override_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    async def override_current_user(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> User:
        user = await session.get(User, current["user_id"])
        assert user is not None
        return user

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_current_user] = override_current_user
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client, session_factory, current, ids
    await engine.dispose()


async def create_profile(
    client: httpx.AsyncClient,
    current: dict[str, uuid.UUID],
    user_id: uuid.UUID,
    *,
    years: int = 5,
    rate: int = 10_000,
) -> uuid.UUID:
    current["user_id"] = user_id
    response = await client.post(
        "/interviewers/me/profile",
        json={
            "title": "Staff Engineer",
            "bio": "Experienced interviewer",
            "years_experience": years,
            "default_rate_minor": rate,
            "currency": "INR",
        },
    )
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["id"])


async def approve_profile(
    client: httpx.AsyncClient,
    current: dict[str, uuid.UUID],
    admin_id: uuid.UUID,
    profile_id: uuid.UUID,
) -> None:
    current["user_id"] = admin_id
    response = await client.patch(
        f"/admin/interviewer-verifications/{profile_id}",
        json={"status": "APPROVED", "notes": "Identity checked"},
    )
    assert response.status_code == 200, response.text


async def create_slot(
    client: httpx.AsyncClient,
    current: dict[str, uuid.UUID],
    user_id: uuid.UUID,
    start: str,
    end: str,
    *,
    price: int | None = None,
) -> httpx.Response:
    current["user_id"] = user_id
    payload: dict[str, object] = {"start_time": start, "end_time": end}
    if price is not None:
        payload.update({"price_minor": price, "currency": "INR"})
    return await client.post("/interviewers/me/slots", json=payload)


@pytest.mark.asyncio
async def test_unverified_interviewer_cannot_publish_and_utc_is_preserved(
    marketplace_context: MarketplaceContext,
) -> None:
    client, _, current, ids = marketplace_context
    profile_id = await create_profile(client, current, ids["first"])
    denied = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T10:00:00+05:30",
        "2027-01-10T11:00:00+05:30",
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "INTERVIEWER_NOT_APPROVED"

    await approve_profile(client, current, ids["admin"], profile_id)
    created = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T10:00:00+05:30",
        "2027-01-10T11:00:00+05:30",
    )
    assert created.status_code == 201, created.text
    assert created.json()["start_time"] == "2027-01-10T04:30:00Z"


@pytest.mark.asyncio
async def test_invalid_and_overlapping_slots_are_rejected(
    marketplace_context: MarketplaceContext,
) -> None:
    client, _, current, ids = marketplace_context
    profile_id = await create_profile(client, current, ids["first"])
    await approve_profile(client, current, ids["admin"], profile_id)

    invalid = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T12:00:00Z",
        "2027-01-10T11:00:00Z",
    )
    assert invalid.status_code == 422

    first = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T10:00:00Z",
        "2027-01-10T11:00:00Z",
    )
    assert first.status_code == 201
    overlap = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T10:30:00Z",
        "2027-01-10T11:30:00Z",
    )
    assert overlap.status_code == 409
    assert overlap.json()["error"]["code"] == "SLOT_OVERLAP"

    adjacent = await create_slot(
        client,
        current,
        ids["first"],
        "2027-01-10T11:00:00Z",
        "2027-01-10T12:00:00Z",
    )
    assert adjacent.status_code == 201


@pytest.mark.asyncio
async def test_slot_ownership_is_enforced(marketplace_context: MarketplaceContext) -> None:
    client, _, current, ids = marketplace_context
    profile_id = await create_profile(client, current, ids["first"])
    await approve_profile(client, current, ids["admin"], profile_id)
    created = await create_slot(
        client,
        current,
        ids["first"],
        "2027-02-01T10:00:00Z",
        "2027-02-01T11:00:00Z",
    )
    slot_id = created.json()["id"]

    current["user_id"] = ids["second"]
    response = await client.patch(
        f"/interviewers/me/slots/{slot_id}",
        json={"start_time": "2027-02-01T12:00:00Z"},
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SLOT_NOT_FOUND"

    current["user_id"] = ids["first"]
    updated = await client.patch(
        f"/interviewers/me/slots/{slot_id}",
        json={"price_minor": 11_000, "currency": "INR"},
    )
    assert updated.status_code == 200
    assert updated.json()["price_minor"] == 11_000
    blocked = await client.delete(f"/interviewers/me/slots/{slot_id}")
    assert blocked.status_code == 200
    assert blocked.json()["status"] == "BLOCKED"
    immutable = await client.patch(
        f"/interviewers/me/slots/{slot_id}",
        json={"price_minor": 12_000, "currency": "INR"},
    )
    assert immutable.status_code == 409
    assert immutable.json()["error"]["code"] == "SLOT_NOT_EDITABLE"


@pytest.mark.asyncio
async def test_public_slots_hide_reserved_booked_and_blocked(
    marketplace_context: MarketplaceContext,
) -> None:
    client, session_factory, current, ids = marketplace_context
    profile_id = await create_profile(client, current, ids["first"])
    await approve_profile(client, current, ids["admin"], profile_id)
    responses = []
    for hour in (10, 12, 14, 16):
        responses.append(
            await create_slot(
                client,
                current,
                ids["first"],
                f"2027-03-01T{hour}:00:00Z",
                f"2027-03-01T{hour + 1}:00:00Z",
            )
        )
    slot_ids = [uuid.UUID(response.json()["id"]) for response in responses]
    async with session_factory() as session:
        slots = list(
            (
                await session.execute(
                    select(AvailabilitySlot).where(AvailabilitySlot.id.in_(slot_ids))
                )
            ).scalars()
        )
        by_id = {slot.id: slot for slot in slots}
        by_id[slot_ids[1]].status = AvailabilityStatus.RESERVED
        by_id[slot_ids[1]].reserved_by = ids["second"]
        by_id[slot_ids[1]].reservation_expires_at = datetime(2027, 3, 1, 11, tzinfo=UTC)
        by_id[slot_ids[2]].status = AvailabilityStatus.BOOKED
        by_id[slot_ids[3]].status = AvailabilityStatus.BLOCKED
        await session.commit()

    public = await client.get(f"/interviewers/{profile_id}/slots")
    assert public.status_code == 200
    assert [slot["id"] for slot in public.json()] == [str(slot_ids[0])]


@pytest.mark.asyncio
async def test_discovery_filters_and_hides_verification_notes(
    marketplace_context: MarketplaceContext,
) -> None:
    client, _, current, ids = marketplace_context
    first_profile = await create_profile(client, current, ids["first"], years=8, rate=12_000)
    second_profile = await create_profile(client, current, ids["second"], years=2, rate=5_000)
    await approve_profile(client, current, ids["admin"], first_profile)
    await approve_profile(client, current, ids["admin"], second_profile)

    current["user_id"] = ids["admin"]
    skill = await client.post("/admin/skills", json={"name": "Python", "slug": "python"})
    skill_id = skill.json()["id"]
    current["user_id"] = ids["first"]
    assert (
        await client.post(
            "/interviewers/me/skills",
            json={"skill_id": skill_id, "years_experience": 8},
        )
    ).status_code == 200

    assert (
        await create_slot(
            client,
            current,
            ids["first"],
            "2027-04-01T10:00:00Z",
            "2027-04-01T11:00:00Z",
            price=12_000,
        )
    ).status_code == 201
    assert (
        await create_slot(
            client,
            current,
            ids["second"],
            "2027-04-01T10:00:00Z",
            "2027-04-01T11:00:00Z",
            price=5_000,
        )
    ).status_code == 201

    search = await client.get(
        "/interviewers",
        params={
            "skill": "python",
            "min_years_experience": 5,
            "min_price_minor": 10_000,
            "available_from": "2027-04-01T09:00:00Z",
            "available_to": "2027-04-01T12:00:00Z",
        },
    )
    assert search.status_code == 200, search.text
    assert [profile["id"] for profile in search.json()] == [str(first_profile)]
    assert "notes" not in search.json()[0]

    public_profile = await client.get(f"/interviewers/{first_profile}")
    assert "notes" not in public_profile.json()
    assert "email" not in public_profile.json()
