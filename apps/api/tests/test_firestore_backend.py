"""Contract tests, run against memory AND the real emulator when configured.

The memory double tests business rules/rollback, not Firestore concurrency.
Set FIRESTORE_EMULATOR_HOST to exercise the actual async transaction adapter.
"""

import asyncio
import json
import os
import uuid
from copy import deepcopy
from datetime import timedelta

import httpx
import pytest
import pytest_asyncio
from google.cloud.firestore_v1 import AsyncClient

from app.core.config import Settings
from app.core.errors import ApiError
from app.firestore_backend.bookings import BookingService, PaymentService
from app.firestore_backend.common import now
from app.firestore_backend.feedback import ReviewService, RubricService
from app.firestore_backend.identity import IdentityService
from app.firestore_backend.interviewers import InterviewerService
from app.firestore_backend.operations import NotificationService, TaskService
from app.firestore_backend.sessions import DesktopAuthService
from app.firestore_backend.store import FirestoreStore, UnitOfWork
from app.integrations.payments import MockPaymentProvider
from app.main import create_app
from app.schemas.bookings import BookingReserveRequest, PaymentCheckoutRequest
from app.schemas.feedback import ReviewCreateRequest, RubricSubmitRequest
from app.schemas.interviewers import (
    AvailabilitySlotCreateRequest,
    AvailabilitySlotUpdateRequest,
    ProfileUpsertRequest,
    VerificationReviewRequest,
)
from app.schemas.sessions import ExchangeDesktopTicketRequest, MintDesktopTicketRequest


class MemoryUnit(UnitOfWork):
    async def get(self, collection, key):
        address = collection, str(key)
        if address in self.pending:
            return deepcopy(self.pending[address])
        return deepcopy(self.store.documents.get(address))

    async def query(self, collection, filters=(), *, limit=100, offset=0, order=None):
        docs = [deepcopy(d) for (c, _), d in self.store.documents.items() if c == collection]
        for field, operator, value in filters:

            def match(d, field=field, operator=operator, value=value):
                actual = d.get(field)
                if operator == "==":
                    return actual == value
                if operator == "array_contains":
                    return value in (actual or [])
                if actual is None:
                    return False
                return {">": actual > value, "<=": actual <= value}[operator]

            docs = [d for d in docs if match(d)]
        if order:
            docs.sort(key=lambda d: d[order.lstrip("-")], reverse=order.startswith("-"))
        return docs[offset : offset + limit]


class MemoryStore(FirestoreStore):
    def __init__(self, settings):
        self.settings = settings
        self.documents = {}
        self.lock = asyncio.Lock()

    def reader(self):
        return MemoryUnit(self)

    async def run(self, callback):
        async with self.lock:
            tx = MemoryUnit(self)
            result = await callback(tx)
            for key, value in tx.pending.items():
                if value is None:
                    self.documents.pop(key, None)
                else:
                    self.documents[key] = deepcopy(value)
            return result


@pytest_asyncio.fixture(params=["memory", "emulator"])
async def store(request):
    settings = Settings(
        app_env="test",
        database_backend="firestore",
        admin_emails=["admin@test.com"],
        rate_limit_enabled=False,
        payment_provider="mock",
    )
    if request.param == "memory":
        yield MemoryStore(settings)
    else:
        host = os.getenv("FIRESTORE_EMULATOR_HOST")
        if not host:
            pytest.skip("Set FIRESTORE_EMULATOR_HOST for real transaction/concurrency tests")
        assert host.startswith(("localhost:", "127.0.0.1:")), "Tests require a local emulator"
        project = f"demo-ir-{uuid.uuid4().hex[:12]}"
        store = FirestoreStore(AsyncClient(project=project), settings)
        try:
            yield store
        finally:
            await store.close()


async def account(store, name):
    return await IdentityService(store).authenticate(
        {
            "uid": name,
            "email": f"{name}@test.com",
            "name": name,
            "email_verified": True,
            "role": "ADMIN",
        }
    )


@pytest_asyncio.fixture
async def setup(store):
    admin = await account(store, "admin")
    interviewer = await account(store, "interviewer")
    candidate = await account(store, "candidate")
    other = await account(store, "other")
    service = InterviewerService(store)
    profile = await service.create_profile(
        interviewer,
        ProfileUpsertRequest(
            title="Engineer",
            default_rate_minor=1000,
            currency="INR",
        ),
    )
    await service.review_verification(
        profile.id, admin, VerificationReviewRequest(status="APPROVED")
    )
    interviewer = await account(store, "interviewer")
    slot = await service.create_slot(
        interviewer,
        AvailabilitySlotCreateRequest(
            start_time=now() + timedelta(minutes=5),
            end_time=now() + timedelta(minutes=65),
        ),
    )
    return store, admin, interviewer, candidate, other, profile, slot


async def reserve(setup):
    store, _, _, candidate, _, _, slot = setup
    return await BookingService(store).reserve_slot(
        candidate, BookingReserveRequest(slot_id=slot["id"])
    )


async def pay(setup, booking, event_id="evt-1", status="PAID", **overrides):
    store, _, _, candidate, *_ = setup
    payment_service = PaymentService(store)
    payment = await store.reader().get("payments", booking.id)
    if not payment:
        await payment_service.create_checkout(candidate, booking.id, PaymentCheckoutRequest())
        payment = await store.reader().get("payments", booking.id)
    body = json.dumps(
        {
            "event_id": event_id,
            "booking_id": str(booking.id),
            "provider_payment_id": payment["provider_payment_id"],
            "amount_minor": booking.price_minor,
            "currency": booking.currency,
            "status": status,
            **overrides,
        }
    ).encode()
    signature = MockPaymentProvider(store.settings.webhook_signing_secret).compute_signature(body)
    return await payment_service.process_webhook("mock", body, {"x-webhook-signature": signature})


async def test_identity_no_claim_escalation_and_disabled_account(store):
    users = await asyncio.gather(*(account(store, "same") for _ in range(3)))
    assert len({u.id for u in users}) == 1
    assert all(u.role == "CANDIDATE" for u in users)

    async def disable(tx):
        doc = await tx.get("users", users[0].id)
        tx.put("users", users[0].id, {**doc, "status": "SUSPENDED"})

    await store.run(disable)
    with pytest.raises(ApiError, match="Account is not active"):
        await account(store, "same")


async def test_unverified_admin_email_does_not_escalate(store):
    user = await IdentityService(store).authenticate({"uid": "x", "email": "admin@test.com"})
    assert user.role == "CANDIDATE"


async def test_email_uniqueness(store):
    await account(store, "candidate")
    with pytest.raises(ApiError) as caught:
        await IdentityService(store).authenticate(
            {"uid": "different", "email": "candidate@test.com"}
        )
    assert caught.value.code == "IDENTITY_CONFLICT"


async def test_simultaneous_reservations_only_one_winner(setup):
    store, _, _, candidate, other, _, slot = setup
    results = await asyncio.gather(
        *(
            BookingService(store).reserve_slot(user, BookingReserveRequest(slot_id=slot["id"]))
            for user in (candidate, other)
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert sum(isinstance(r, ApiError) and r.code == "SLOT_ALREADY_RESERVED" for r in results) == 1


async def test_concurrent_overlapping_slot_creation(setup):
    store, _, interviewer, *_ = setup
    start = now() + timedelta(days=1)
    results = await asyncio.gather(
        *(
            InterviewerService(store).create_slot(
                interviewer,
                AvailabilitySlotCreateRequest(
                    start_time=start + timedelta(minutes=i),
                    end_time=start + timedelta(minutes=60 + i),
                ),
            )
            for i in range(2)
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert any(isinstance(r, ApiError) and r.code == "SLOT_OVERLAP" for r in results)


async def test_booked_slot_cannot_be_edited(setup):
    store, _, interviewer, *_ = setup
    await reserve(setup)
    with pytest.raises(ApiError) as caught:
        await InterviewerService(store).update_slot(
            interviewer,
            setup[-1]["id"],
            AvailabilitySlotUpdateRequest(price_minor=1, currency="INR"),
        )
    assert caught.value.code == "SLOT_NOT_EDITABLE"


async def test_duplicate_webhooks_and_checkout_are_idempotent(setup):
    store, _, _, candidate, *_ = setup
    booking = await reserve(setup)
    responses = await asyncio.gather(
        *(
            PaymentService(store).create_checkout(candidate, booking.id, PaymentCheckoutRequest())
            for _ in range(2)
        )
    )
    assert responses[0].checkout_url == responses[1].checkout_url
    results = await asyncio.gather(pay(setup, booking), pay(setup, booking))
    assert sorted(r.status for r in results) == ["confirmed", "duplicate"]
    assert (await store.reader().get("bookings", booking.id))["status"] == "CONFIRMED"
    assert len(await store.reader().query("notifications")) == 2
    await pay(setup, booking, event_id="evt-failed", status="FAILED")
    assert (await store.reader().get("payments", booking.id))["status"] == "PAID"


async def test_invalid_payment_cannot_confirm(setup):
    store, *_ = setup
    booking = await reserve(setup)
    with pytest.raises(ApiError):
        await pay(setup, booking, amount_minor=1)
    assert (await store.reader().get("bookings", booking.id))["status"] == "PENDING_PAYMENT"
    assert await store.reader().query("payment_events") == []
    with pytest.raises(ApiError):
        await PaymentService(store).process_webhook("mock", b"{}", {})


async def test_expiry_rebooking_and_late_payment_do_not_steal_slot(setup):
    store, _, _, candidate, other, _, slot = setup
    old = await reserve(setup)
    await PaymentService(store).create_checkout(candidate, old.id, PaymentCheckoutRequest())

    async def expire(tx):
        doc = await tx.get("slots", slot["id"])
        tx.put("slots", slot["id"], {**doc, "reservation_expires_at": now() - timedelta(seconds=1)})

    await store.run(expire)
    newer = await BookingService(store).reserve_slot(
        other, BookingReserveRequest(slot_id=slot["id"])
    )
    result = await pay(setup, old)
    assert result.status == "refund_pending"
    assert (await store.reader().get("slots", slot["id"]))["booking_id"] == str(newer.id)
    assert await TaskService(store).process_refunds() == 1
    assert await TaskService(store).process_refunds() == 0
    assert (await store.reader().get("slots", slot["id"]))["booking_id"] == str(newer.id)
    assert (await store.reader().get("payments", old.id))["status"] == "REFUNDED"


async def test_feedback_privacy_and_one_review_per_booking(setup):
    store, _, interviewer, candidate, other, profile, _ = setup
    booking = await reserve(setup)
    request = RubricSubmitRequest(
        technical_score=4,
        problem_solving_score=3,
        communication_score=5,
        detailed_feedback="Good",
        private_interviewer_notes="SECRET",
    )
    with pytest.raises(ApiError):
        await RubricService(store).submit_rubric(interviewer, booking.id, request)
    await pay(setup, booking)
    await RubricService(store).submit_rubric(interviewer, booking.id, request)
    public = await RubricService(store).get_candidate_feedback(candidate, booking.id)
    assert "SECRET" not in public.model_dump_json()
    assert "private_interviewer_notes" not in await store.reader().get("feedback", booking.id)
    with pytest.raises(ApiError):
        await RubricService(store).get_interviewer_rubric(candidate, booking.id)
    with pytest.raises(ApiError):
        await RubricService(store).get_candidate_feedback(other, booking.id)
    results = await asyncio.gather(
        *(
            ReviewService(store).create_review(candidate, booking.id, ReviewCreateRequest(rating=5))
            for _ in range(2)
        ),
        return_exceptions=True,
    )
    assert sum(not isinstance(r, Exception) for r in results) == 1
    summary = await ReviewService(store).get_interviewer_rating_summary(profile.id)
    assert summary["total_reviews"] == 1
    assert summary["average_rating"] == 5
    assert (await ReviewService(store).get_interviewer_rating_summary(interviewer.id))[
        "total_reviews"
    ] == 1
    reviews = await ReviewService(store).list_interviewer_reviews(profile.id)
    assert len(reviews) == 1
    assert reviews[0]["interviewer_id"] == str(interviewer.id)


class TicketRedis:
    def __init__(self):
        self.values = {}

    async def set(self, key, value, ex):
        self.values[key] = value

    async def getdel(self, key):
        return self.values.pop(key, None)


async def test_desktop_ticket_replay_and_session_creation(setup):
    store, _, interviewer, candidate, *_ = setup
    booking = await reserve(setup)
    await pay(setup, booking)
    redis = TicketRedis()
    service = DesktopAuthService(store)
    tickets = [
        await service.mint_desktop_ticket(
            user, MintDesktopTicketRequest(booking_id=booking.id), redis
        )
        for user in (candidate, interviewer)
    ]
    sessions = await asyncio.gather(
        *(
            service.exchange_desktop_ticket(
                ExchangeDesktopTicketRequest(ticket=t.ticket, booking_id=booking.id), redis
            )
            for t in tickets
        )
    )
    assert sessions[0].session_id == sessions[1].session_id
    assert (await store.reader().get("bookings", booking.id))["status"] == "IN_PROGRESS"
    with pytest.raises(ApiError) as caught:
        await service.exchange_desktop_ticket(
            ExchangeDesktopTicketRequest(ticket=tickets[0].ticket), redis
        )
    assert caught.value.code == "INVALID_OR_EXPIRED_TICKET"


async def test_transaction_rolls_back_pending_writes(store):
    async def fail(tx):
        tx.put("test", "rollback", {"value": 1})
        raise ApiError("TEST", "rollback")

    with pytest.raises(ApiError):
        await store.run(fail)
    assert await store.reader().get("test", "rollback") is None


async def test_http_contract_admin_and_tasks(setup, monkeypatch):
    store, _, _, candidate, *_ = setup
    import app.core.auth as auth

    async def verify(token):
        return {"uid": token, "email": f"{token}@test.com", "email_verified": True}

    monkeypatch.setattr(auth, "verify_firebase_id_token", verify)
    app = create_app(store.settings)
    app.state.firestore_store = store
    app.state.redis = None
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        headers = {"Authorization": "Bearer candidate"}
        response = await client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["id"] == str(candidate.id)
        for path in (
            "/interviewers",
            "/skills",
            "/api/v1/interviewers",
            "/notifications/me",
            "/bookings/me",
        ):
            response = await client.get(path, headers=headers)
            assert response.status_code == 200, response.text
        assert (await client.get("/admin/users", headers=headers)).status_code == 403
        assert (
            await client.post("/internal/tasks/process", json={"task_type": "expire_reservations"})
        ).status_code == 401
        for path in (
            "/admin/users",
            "/admin/verifications",
            "/admin/bookings",
            "/admin/payments",
            "/admin/slots",
            "/admin/audit-logs",
        ):
            response = await client.get(path, headers={"Authorization": "Bearer admin"})
            assert response.status_code == 200, response.text


async def test_notification_ownership(setup):
    store, _, _, candidate, other, *_ = setup
    booking = await reserve(setup)
    await pay(setup, booking)
    service = NotificationService(store)
    notifications = await service.list_in_app_notifications(candidate)
    assert len(notifications) == 1
    with pytest.raises(ApiError):
        await service.mark_as_read(other, notifications[0]["id"])
    assert await service.mark_all_as_read(candidate) == 1
    assert await service.list_in_app_notifications(candidate, unread_only=True) == []


async def test_expiry_worker_racing_with_webhook(setup):
    store, _, _, candidate, _, _, slot = setup
    booking = await reserve(setup)
    await PaymentService(store).create_checkout(candidate, booking.id, PaymentCheckoutRequest())

    async def expire(tx):
        doc = await tx.get("slots", slot["id"])
        tx.put("slots", slot["id"], {**doc, "reservation_expires_at": now() - timedelta(seconds=1)})

    await store.run(expire)
    await asyncio.gather(BookingService(store).expire_stale_reservations(), pay(setup, booking))
    assert (await store.reader().get("bookings", booking.id))["status"] == "EXPIRED"
    assert (await store.reader().get("slots", slot["id"]))["status"] == "AVAILABLE"
    assert len(await store.reader().query("refund_jobs")) == 1


async def test_cancel_after_ticket_mint_blocks_exchange(setup):
    store, _, _, candidate, *_ = setup
    booking = await reserve(setup)
    await pay(setup, booking)
    redis = TicketRedis()
    service = DesktopAuthService(store)
    ticket = await service.mint_desktop_ticket(
        candidate, MintDesktopTicketRequest(booking_id=booking.id), redis
    )
    await BookingService(store).cancel_booking(candidate, booking.id)
    with pytest.raises(ApiError) as caught:
        await service.exchange_desktop_ticket(
            ExchangeDesktopTicketRequest(ticket=ticket.ticket), redis
        )
    assert caught.value.code == "BOOKING_NOT_JOINABLE"
    assert len(await store.reader().query("refund_jobs")) == 1


async def test_directory_prices_filter_slots_not_profile_default(setup):
    store, _, interviewer, _, _, profile, slot = setup
    await InterviewerService(store).update_slot(
        interviewer, slot["id"], AvailabilitySlotUpdateRequest(price_minor=200, currency="INR")
    )
    profiles = await InterviewerService(store).list_public_profiles(max_price_minor=300)
    assert [p["id"] for p in profiles] == [str(profile.id)]
    assert await InterviewerService(store).list_public_profiles(min_price_minor=1500) == []


async def test_firestore_lifespan_does_not_construct_sql_engine(monkeypatch):
    import app.main as main

    def forbidden(*args, **kwargs):
        raise AssertionError("Firestore startup must not create a SQL engine")

    class RedisStub:
        async def aclose(self):
            pass

    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
    monkeypatch.setattr(main, "create_database_engine", forbidden)
    monkeypatch.setattr(main, "create_redis_client", lambda _: RedisStub())
    app = create_app(
        Settings(app_env="test", database_backend="firestore", firestore_project_id="demo-startup")
    )
    async with app.router.lifespan_context(app):
        assert isinstance(app.state.firestore_store, FirestoreStore)
        assert not hasattr(app.state, "db_engine")


async def test_production_rejects_emulator(monkeypatch):
    monkeypatch.setenv("FIRESTORE_EMULATOR_HOST", "127.0.0.1:8080")
    app = create_app(
        Settings(
            app_env="production", database_backend="firestore", firestore_project_id="demo-startup"
        )
    )
    with pytest.raises(ValueError, match="forbidden"):
        async with app.router.lifespan_context(app):
            pass


async def test_notification_channels_are_respected_and_deduplicated(store):
    user = await account(store, "candidate")
    service = TaskService(store)
    payload = {
        "recipient_user_id": str(user.id),
        "event_type": "TEST",
        "reference_id": "channel-test",
        "channels": ["IN_APP"],
    }
    await service.process_task("dispatch_notification", payload)
    assert len(await store.reader().query("notifications")) == 1
    assert await store.reader().query("notification_outbox") == []
    payload["channels"] = ["FCM"]
    await service.process_task("dispatch_notification", payload)
    await service.process_task("dispatch_notification", payload)
    outbox = await store.reader().query("notification_outbox")
    assert len(outbox) == 1
    assert outbox[0]["channels"] == ["FCM"]
    assert outbox[0]["status"] == "PENDING"
