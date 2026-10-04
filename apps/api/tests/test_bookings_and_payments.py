import json
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Annotated, TypeAlias
from unittest.mock import MagicMock, patch

import httpx
import pytest
import pytest_asyncio
import stripe
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.auth import get_current_user
from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_session
from app.integrations.payments import (
    MockPaymentProvider,
    StripePaymentProvider,
)
from app.main import create_app
from app.models.availability import AvailabilitySlot, AvailabilityStatus
from app.models.booking import Booking, BookingStatus, Payment, PaymentStatus
from app.models.identity import InterviewerProfile, User, UserRole
from app.workers.reservation_expiry import expire_reservations_task

SessionFactory: TypeAlias = async_sessionmaker[AsyncSession]
BookingTestContext: TypeAlias = tuple[
    httpx.AsyncClient,
    SessionFactory,
    dict[str, uuid.UUID],
    dict[str, uuid.UUID],
    MockPaymentProvider,
]


@pytest_asyncio.fixture
async def booking_context() -> AsyncIterator[BookingTestContext]:
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
        "candidate_1": User(
            firebase_uid="candidate_1_uid",
            email="candidate1@example.com",
            full_name="Candidate One",
            role=UserRole.CANDIDATE,
            email_verified=True,
        ),
        "candidate_2": User(
            firebase_uid="candidate_2_uid",
            email="candidate2@example.com",
            full_name="Candidate Two",
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
            title="Principal Architect",
            years_experience=10,
            default_rate_minor=15_000,
            currency="INR",
            is_verified=True,
        )
        session.add(profile)
        await session.commit()
        ids = {name: user.id for name, user in users.items()}
        ids["profile_id"] = profile.id

    current = {"user_id": ids["candidate_1"]}
    settings = Settings(
        app_env="test",
        reservation_ttl_minutes=10,
        webhook_signing_secret="test_secret_key_12345",
        payment_provider="mock",
        stripe_secret_key="sk_test_fake_stripe_secret_key_123",
        stripe_webhook_secret="whsec_test_stripe_webhook_secret_12345",
    )
    app = create_app(settings)
    payment_provider = MockPaymentProvider(secret=settings.webhook_signing_secret)

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
        yield client, session_factory, current, ids, payment_provider
    await engine.dispose()


async def create_slot_in_db(
    session_factory: SessionFactory,
    profile_id: uuid.UUID,
    *,
    start_offset_hours: int = 24,
    duration_hours: int = 1,
    price_minor: int = 15_000,
    currency: str = "INR",
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE,
    reserved_by: uuid.UUID | None = None,
    reservation_expires_at: datetime | None = None,
) -> AvailabilitySlot:
    now = datetime.now(UTC)
    start_time = now + timedelta(hours=start_offset_hours)
    end_time = start_time + timedelta(hours=duration_hours)

    async with session_factory() as session:
        slot = AvailabilitySlot(
            interviewer_id=profile_id,
            start_time=start_time,
            end_time=end_time,
            price_minor=price_minor,
            currency=currency,
            status=status,
            reserved_by=reserved_by,
            reservation_expires_at=reservation_expires_at,
        )
        session.add(slot)
        await session.commit()
        await session.refresh(slot)
        return slot


@pytest.mark.asyncio
async def test_slot_reservation_success_and_price_snapshot(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=20_000)

    current["user_id"] = ids["candidate_1"]
    response = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert response.status_code == 201, response.text
    data = response.json()

    assert data["slot_id"] == str(slot.id)
    assert data["candidate_id"] == str(ids["candidate_1"])
    assert data["interviewer_id"] == str(ids["interviewer"])
    assert data["status"] == "PENDING_PAYMENT"
    assert data["price_minor"] == 20_000
    assert data["currency"] == "INR"
    assert data["reservation_expires_at"] is not None

    # Verify slot is updated in DB
    async with session_factory() as session:
        updated_slot = await session.get(AvailabilitySlot, slot.id)
        assert updated_slot is not None
        assert updated_slot.status == AvailabilityStatus.RESERVED
        assert updated_slot.reserved_by == ids["candidate_1"]
        assert updated_slot.reservation_expires_at is not None

        # Change slot price in DB - Booking price snapshot must remain unchanged
        updated_slot.price_minor = 35_000
        await session.commit()

        booking = await session.get(Booking, uuid.UUID(data["id"]))
        assert booking is not None
        assert booking.price_minor == 20_000


@pytest.mark.asyncio
async def test_concurrent_reservations_only_one_succeeds(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"])

    # First user reserves
    current["user_id"] = ids["candidate_1"]
    res1 = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert res1.status_code == 201

    # Second user attempts to reserve the same slot
    current["user_id"] = ids["candidate_2"]
    res2 = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "SLOT_ALREADY_RESERVED"


@pytest.mark.asyncio
async def test_cannot_book_own_slot(booking_context: BookingTestContext) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"])

    # Interviewer tries to book their own slot
    current["user_id"] = ids["interviewer"]
    response = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "CANNOT_BOOK_OWN_SLOT"


@pytest.mark.asyncio
async def test_expired_reservation_becomes_available_for_new_booking(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    # Slot was reserved in the past
    past_expiry = datetime.now(UTC) - timedelta(minutes=5)
    slot = await create_slot_in_db(
        session_factory,
        ids["profile_id"],
        status=AvailabilityStatus.RESERVED,
        reserved_by=ids["candidate_1"],
        reservation_expires_at=past_expiry,
    )

    # Candidate 2 attempts to reserve the slot whose reservation expired
    current["user_id"] = ids["candidate_2"]
    response = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["candidate_id"] == str(ids["candidate_2"])
    assert data["status"] == "PENDING_PAYMENT"


@pytest.mark.asyncio
async def test_payment_checkout_uses_booking_snapshot_and_enforces_ownership(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=12_500)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert reserve_res.status_code == 201
    booking_id = reserve_res.json()["id"]

    # Candidate 2 tries to checkout Candidate 1's booking -> Forbidden
    current["user_id"] = ids["candidate_2"]
    forbidden_res = await client.post(f"/api/v1/payments/{booking_id}/checkout", json={})
    assert forbidden_res.status_code == 403
    assert forbidden_res.json()["error"]["code"] == "FORBIDDEN"

    # Candidate 1 checks out
    current["user_id"] = ids["candidate_1"]
    checkout_res = await client.post(
        f"/api/v1/payments/{booking_id}/checkout",
        json={"success_url": "http://frontend/success", "cancel_url": "http://frontend/cancel"},
    )
    assert checkout_res.status_code == 200, checkout_res.text
    checkout_data = checkout_res.json()
    assert checkout_data["booking_id"] == booking_id
    assert checkout_data["amount_minor"] == 12_500
    assert checkout_data["currency"] == "INR"
    assert checkout_data["status"] == "PENDING"
    assert "checkout_url" in checkout_data


@pytest.mark.asyncio
async def test_webhook_payment_success_confirms_booking_and_books_slot(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, provider = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=18_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "payment_intent.succeeded",
        "booking_id": booking_id,
        "provider_payment_id": f"pi_{uuid.uuid4().hex}",
        "amount_minor": 18_000,
        "currency": "INR",
        "status": "PAID",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    signature = provider.compute_signature(payload_bytes)

    webhook_res = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
        },
    )
    assert webhook_res.status_code == 200, webhook_res.text
    assert webhook_res.json()["status"] == "processed"

    # Verify DB state
    async with session_factory() as session:
        booking = await session.get(Booking, uuid.UUID(booking_id))
        assert booking is not None
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.confirmed_at is not None

        db_slot = await session.get(AvailabilitySlot, slot.id)
        assert db_slot is not None
        assert db_slot.status == AvailabilityStatus.BOOKED
        assert db_slot.reserved_by is None
        assert db_slot.reservation_expires_at is None

        payment = (
            await session.execute(
                select(Payment).where(Payment.booking_id == uuid.UUID(booking_id))
            )
        ).scalar_one_or_none()
        assert payment is not None
        assert payment.status == PaymentStatus.PAID
        assert payment.amount_minor == 18_000


@pytest.mark.asyncio
async def test_webhook_deduplication_and_replay_harmless(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, provider = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=10_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    event_id = f"evt_{uuid.uuid4().hex}"
    event_payload = {
        "event_id": event_id,
        "event_type": "payment_intent.succeeded",
        "booking_id": booking_id,
        "provider_payment_id": f"pi_{uuid.uuid4().hex}",
        "amount_minor": 10_000,
        "currency": "INR",
        "status": "PAID",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    signature = provider.compute_signature(payload_bytes)

    # First delivery
    res1 = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
    )
    assert res1.status_code == 200
    assert res1.json()["status"] == "processed"

    # Replay identical webhook
    res2 = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "duplicate_ignored"


@pytest.mark.asyncio
async def test_webhook_invalid_signature_rejected(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"])

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "payment_intent.succeeded",
        "booking_id": booking_id,
        "amount_minor": 15_000,
        "currency": "INR",
        "status": "PAID",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")

    response = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": "forged_invalid_signature",
        },
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_WEBHOOK_SIGNATURE"


@pytest.mark.asyncio
async def test_failed_payment_webhook_does_not_book_slot(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, provider = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=15_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "payment_intent.payment_failed",
        "booking_id": booking_id,
        "provider_payment_id": f"pi_{uuid.uuid4().hex}",
        "amount_minor": 15_000,
        "currency": "INR",
        "status": "FAILED",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    signature = provider.compute_signature(payload_bytes)

    response = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
    )
    assert response.status_code == 200

    async with session_factory() as session:
        booking = await session.get(Booking, uuid.UUID(booking_id))
        assert booking is not None
        assert booking.status == BookingStatus.PENDING_PAYMENT

        db_slot = await session.get(AvailabilitySlot, slot.id)
        assert db_slot is not None
        assert db_slot.status != AvailabilityStatus.BOOKED


@pytest.mark.asyncio
async def test_webhook_amount_mismatch_fails_and_does_not_confirm(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, provider = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=15_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    # Webhook attempts to confirm with 10_000 instead of 15_000
    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "payment_intent.succeeded",
        "booking_id": booking_id,
        "provider_payment_id": f"pi_{uuid.uuid4().hex}",
        "amount_minor": 10_000,
        "currency": "INR",
        "status": "PAID",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    signature = provider.compute_signature(payload_bytes)

    response = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": signature},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "PAYMENT_AMOUNT_MISMATCH"

    async with session_factory() as session:
        booking = await session.get(Booking, uuid.UUID(booking_id))
        assert booking is not None
        assert booking.status == BookingStatus.PENDING_PAYMENT


@pytest.mark.asyncio
async def test_reservation_expiry_task_cleans_up_stale_records(
    booking_context: BookingTestContext,
) -> None:
    _, session_factory, _, ids, _ = booking_context
    past_expiry = datetime.now(UTC) - timedelta(minutes=15)
    slot = await create_slot_in_db(
        session_factory,
        ids["profile_id"],
        status=AvailabilityStatus.RESERVED,
        reserved_by=ids["candidate_1"],
        reservation_expires_at=past_expiry,
    )

    async with session_factory() as session:
        booking = Booking(
            id=uuid.uuid4(),
            slot_id=slot.id,
            candidate_id=ids["candidate_1"],
            interviewer_id=ids["interviewer"],
            status=BookingStatus.PENDING_PAYMENT,
            price_minor=slot.price_minor,
            currency=slot.currency,
            created_at=past_expiry,
        )
        session.add(booking)
        await session.commit()
        booking_id = booking.id

    async with session_factory() as session:
        expired_count = await expire_reservations_task(session)
        assert expired_count > 0

    async with session_factory() as session:
        db_slot = await session.get(AvailabilitySlot, slot.id)
        assert db_slot is not None
        assert db_slot.status == AvailabilityStatus.AVAILABLE
        assert db_slot.reserved_by is None
        assert db_slot.reservation_expires_at is None

        db_booking = await session.get(Booking, booking_id)
        assert db_booking is not None
        assert db_booking.status == BookingStatus.EXPIRED


@pytest.mark.asyncio
async def test_get_and_list_bookings_endpoints(booking_context: BookingTestContext) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"])

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    # Candidate 1 can fetch their booking
    get_res = await client.get(f"/api/v1/bookings/{booking_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == booking_id

    # Candidate 1 can list their bookings
    list_res = await client.get("/api/v1/bookings/me")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
    assert any(b["id"] == booking_id for b in list_res.json())

    # Candidate 2 cannot access Candidate 1's booking
    current["user_id"] = ids["candidate_2"]
    unauth_res = await client.get(f"/api/v1/bookings/{booking_id}")
    assert unauth_res.status_code == 403
    assert unauth_res.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_slot_status_edge_cases_rejected(booking_context: BookingTestContext) -> None:
    client, session_factory, current, ids, _ = booking_context
    current["user_id"] = ids["candidate_1"]

    # Past slot
    past_slot = await create_slot_in_db(session_factory, ids["profile_id"], start_offset_hours=-2)
    res_past = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(past_slot.id)})
    assert res_past.status_code == 400
    assert res_past.json()["error"]["code"] == "SLOT_IN_PAST"

    # Booked slot
    booked_slot = await create_slot_in_db(
        session_factory, ids["profile_id"], status=AvailabilityStatus.BOOKED
    )
    res_booked = await client.post(
        "/api/v1/bookings/reserve", json={"slot_id": str(booked_slot.id)}
    )
    assert res_booked.status_code == 409
    assert res_booked.json()["error"]["code"] == "SLOT_ALREADY_BOOKED"

    # Blocked slot
    blocked_slot = await create_slot_in_db(
        session_factory, ids["profile_id"], status=AvailabilityStatus.BLOCKED
    )
    res_blocked = await client.post(
        "/api/v1/bookings/reserve", json={"slot_id": str(blocked_slot.id)}
    )
    assert res_blocked.status_code == 409
    assert res_blocked.json()["error"]["code"] == "SLOT_UNAVAILABLE"


@pytest.mark.asyncio
async def test_booking_cancellation_and_refund_lifecycle(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, provider = booking_context

    # Test Cancellation of PENDING_PAYMENT booking
    slot1 = await create_slot_in_db(session_factory, ids["profile_id"])
    current["user_id"] = ids["candidate_1"]
    reserve_res1 = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot1.id)})
    booking_id1 = uuid.UUID(reserve_res1.json()["id"])

    async with session_factory() as session:
        from app.services.bookings import BookingService, PaymentService

        service = BookingService(session)
        candidate = await session.get(User, ids["candidate_1"])
        assert candidate is not None
        cancelled_booking = await service.cancel_booking(candidate, booking_id1)
        assert cancelled_booking.status == BookingStatus.CANCELLED

        # Slot is now available again
        db_slot1 = await session.get(AvailabilitySlot, slot1.id)
        assert db_slot1 is not None
        assert db_slot1.status == AvailabilityStatus.AVAILABLE

    # Test Refund of CONFIRMED booking with PAID payment
    slot2 = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=20_000)
    reserve_res2 = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot2.id)})
    booking_id2 = reserve_res2.json()["id"]

    # Confirm via webhook
    event_payload = {
        "event_id": f"evt_{uuid.uuid4().hex}",
        "event_type": "payment_intent.succeeded",
        "booking_id": booking_id2,
        "provider_payment_id": f"pi_{uuid.uuid4().hex}",
        "amount_minor": 20_000,
        "currency": "INR",
        "status": "PAID",
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")
    sig = provider.compute_signature(payload_bytes)
    hook_res = await client.post(
        "/api/v1/webhooks/payments/mock",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Webhook-Signature": sig},
    )
    assert hook_res.status_code == 200

    # Execute refund
    async with session_factory() as session:
        payment_service = PaymentService(session)
        candidate = await session.get(User, ids["candidate_1"])
        assert candidate is not None
        refunded_payment = await payment_service.refund_payment(candidate, uuid.UUID(booking_id2))
        assert refunded_payment.status == PaymentStatus.REFUNDED
        assert refunded_payment.refunded_at is not None

        db_booking2 = await session.get(Booking, uuid.UUID(booking_id2))
        assert db_booking2 is not None
        assert db_booking2.status == BookingStatus.REFUNDED

        db_slot2 = await session.get(AvailabilitySlot, slot2.id)
        assert db_slot2 is not None
        assert db_slot2.status == AvailabilityStatus.AVAILABLE


@pytest.mark.asyncio
async def test_stripe_checkout_success(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=25_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    assert reserve_res.status_code == 201
    booking_id = reserve_res.json()["id"]

    mock_session = MagicMock()
    mock_session.id = "cs_test_stripe_checkout_123"
    mock_session.url = "https://checkout.stripe.com/c/pay/cs_test_stripe_checkout_123"
    mock_session.payment_intent = "pi_test_stripe_intent_123"
    mock_session.expires_at = int((datetime.now(UTC) + timedelta(minutes=30)).timestamp())
    mock_session.to_dict = MagicMock(return_value={"id": mock_session.id})

    with patch("stripe.checkout.Session.create", return_value=mock_session) as mock_create:
        checkout_res = await client.post(
            f"/api/v1/payments/{booking_id}/checkout",
            json={
                "provider": "stripe",
                "success_url": "http://frontend/success",
                "cancel_url": "http://frontend/cancel",
            },
        )
        assert checkout_res.status_code == 200, checkout_res.text
        checkout_data = checkout_res.json()
        assert checkout_data["booking_id"] == booking_id
        assert checkout_data["provider"] == "stripe"
        expected_url = "https://checkout.stripe.com/c/pay/cs_test_stripe_checkout_123"
        assert checkout_data["checkout_url"] == expected_url
        assert checkout_data["provider_checkout_session_id"] == "cs_test_stripe_checkout_123"
        assert checkout_data["amount_minor"] == 25_000
        assert checkout_data["currency"] == "INR"
        assert checkout_data["status"] == "PENDING"
        mock_create.assert_called_once()


@pytest.mark.asyncio
async def test_stripe_webhook_checkout_session_completed_confirms_booking(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=15_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    payment_intent_id = f"pi_test_{uuid.uuid4().hex}"
    event_payload = {
        "id": f"evt_test_{uuid.uuid4().hex}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{uuid.uuid4().hex}",
                "client_reference_id": booking_id,
                "payment_status": "paid",
                "amount_total": 15_000,
                "currency": "inr",
                "payment_intent": payment_intent_id,
                "metadata": {"booking_id": booking_id},
            }
        },
    }
    payload_str = json.dumps(event_payload)
    payload_bytes = payload_str.encode("utf-8")
    secret = "whsec_test_stripe_webhook_secret_12345"
    now_ts = int(datetime.now(UTC).timestamp())
    sig = stripe.WebhookSignature._compute_signature(f"{now_ts}.{payload_str}", secret)
    sig_header = f"t={now_ts},v1={sig}"

    webhook_res = await client.post(
        "/api/v1/webhooks/payments/stripe",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_header,
        },
    )
    assert webhook_res.status_code == 200, webhook_res.text
    assert webhook_res.json()["status"] == "processed"

    # Verify DB state
    async with session_factory() as session:
        booking = await session.get(Booking, uuid.UUID(booking_id))
        assert booking is not None
        assert booking.status == BookingStatus.CONFIRMED
        assert booking.confirmed_at is not None

        db_slot = await session.get(AvailabilitySlot, slot.id)
        assert db_slot is not None
        assert db_slot.status == AvailabilityStatus.BOOKED

        payment = (
            await session.execute(
                select(Payment).where(Payment.booking_id == uuid.UUID(booking_id))
            )
        ).scalar_one_or_none()
        assert payment is not None
        assert payment.provider == "stripe"
        assert payment.status == PaymentStatus.PAID
        assert payment.amount_minor == 15_000
        assert payment.provider_payment_id == payment_intent_id


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature_rejected(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=15_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    event_payload = {
        "id": "evt_tampered_123",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "client_reference_id": booking_id,
                "payment_status": "paid",
                "amount_total": 15_000,
                "currency": "inr",
                "metadata": {"booking_id": booking_id},
            }
        },
    }
    payload_bytes = json.dumps(event_payload).encode("utf-8")

    webhook_res = await client.post(
        "/api/v1/webhooks/payments/stripe",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1700000000,v1=tampered_signature_hex",
        },
    )
    assert webhook_res.status_code == 400
    assert webhook_res.json()["error"]["code"] == "INVALID_WEBHOOK_SIGNATURE"


@pytest.mark.asyncio
async def test_stripe_webhook_amount_mismatch_rejected(
    booking_context: BookingTestContext,
) -> None:
    client, session_factory, current, ids, _ = booking_context
    slot = await create_slot_in_db(session_factory, ids["profile_id"], price_minor=15_000)

    current["user_id"] = ids["candidate_1"]
    reserve_res = await client.post("/api/v1/bookings/reserve", json={"slot_id": str(slot.id)})
    booking_id = reserve_res.json()["id"]

    # Candidate was charged 9_999 instead of expected 15_000
    event_payload = {
        "id": f"evt_test_{uuid.uuid4().hex}",
        "object": "event",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": f"cs_test_{uuid.uuid4().hex}",
                "client_reference_id": booking_id,
                "payment_status": "paid",
                "amount_total": 9_999,
                "currency": "inr",
                "payment_intent": f"pi_test_{uuid.uuid4().hex}",
                "metadata": {"booking_id": booking_id},
            }
        },
    }
    payload_str = json.dumps(event_payload)
    payload_bytes = payload_str.encode("utf-8")
    secret = "whsec_test_stripe_webhook_secret_12345"
    now_ts = int(datetime.now(UTC).timestamp())
    sig = stripe.WebhookSignature._compute_signature(f"{now_ts}.{payload_str}", secret)
    sig_header = f"t={now_ts},v1={sig}"

    webhook_res = await client.post(
        "/api/v1/webhooks/payments/stripe",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_header,
        },
    )
    assert webhook_res.status_code == 400
    assert webhook_res.json()["error"]["code"] == "PAYMENT_AMOUNT_MISMATCH"


@pytest.mark.asyncio
async def test_stripe_refund_unit() -> None:
    provider = StripePaymentProvider(
        secret_key="sk_test_fake_secret_key",
        webhook_secret="whsec_test_fake_webhook_secret",
    )
    mock_refund = MagicMock()
    mock_refund.id = "re_test_stripe_123"
    mock_refund.amount = 15_000
    mock_refund.currency = "inr"
    mock_refund.status = "succeeded"
    mock_refund.to_dict = MagicMock(return_value={"id": mock_refund.id})

    with patch("stripe.Refund.create", return_value=mock_refund) as mock_create:
        res = await provider.refund(
            provider_payment_id="pi_test_stripe_intent_123",
            amount_minor=15_000,
            currency="INR",
            reason="requested_by_customer",
        )
        assert res.refund_id == "re_test_stripe_123"
        assert res.amount_minor == 15_000
        assert res.currency == "INR"
        assert res.status == "succeeded"
        mock_create.assert_called_once_with(
            amount=15_000,
            api_key="sk_test_fake_secret_key",
            payment_intent="pi_test_stripe_intent_123",
            reason="requested_by_customer",
        )
