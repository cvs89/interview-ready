"""Explicit, isolated hosted smoke test. Never writes marketplace collections.

Run from apps/api with --confirm-test-writes. Uses ADC normally; the optional
--gcloud-credentials flag obtains a short-lived CLI token in memory only.
All created documents live below a newly-created _smoke_tests/{random-id} root
and are deleted in finally. No real Firebase Auth accounts or payments are made.
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import uuid
from datetime import timedelta
from pathlib import Path
from typing import Any

from google.cloud.firestore_v1 import AsyncClient
from google.oauth2.credentials import Credentials

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import Settings  # noqa: E402
from app.firestore_backend.bookings import BookingService, PaymentService  # noqa: E402
from app.firestore_backend.common import now  # noqa: E402
from app.firestore_backend.feedback import ReviewService, RubricService  # noqa: E402
from app.firestore_backend.identity import IdentityService  # noqa: E402
from app.firestore_backend.interviewers import InterviewerService  # noqa: E402
from app.firestore_backend.store import FirestoreStore  # noqa: E402
from app.integrations.payments import MockPaymentProvider  # noqa: E402
from app.schemas.bookings import BookingReserveRequest, PaymentCheckoutRequest  # noqa: E402
from app.schemas.feedback import ReviewCreateRequest, RubricSubmitRequest  # noqa: E402
from app.schemas.interviewers import (  # noqa: E402
    AvailabilitySlotCreateRequest,
    ProfileUpsertRequest,
    VerificationReviewRequest,
)


class IsolatedClient:
    def __init__(self, client: AsyncClient, root: Any) -> None:
        self.client = client
        self.root = root
        self.collections: set[str] = set()

    def collection(self, name: str) -> Any:
        self.collections.add(name)
        return self.root.collection(name)

    def transaction(self, **kwargs: Any) -> Any:
        return self.client.transaction(**kwargs)


async def run(args: argparse.Namespace) -> None:
    if os.getenv("FIRESTORE_EMULATOR_HOST"):
        raise RuntimeError("Unset FIRESTORE_EMULATOR_HOST for a hosted test")
    credentials = None
    if args.gcloud_credentials:
        result = await asyncio.to_thread(
            subprocess.run,
            ["gcloud", "auth", "print-access-token", f"--project={args.project}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode or not result.stdout.strip():
            raise RuntimeError("Could not obtain short-lived CLI credentials")
        credentials = Credentials(token=result.stdout.strip(), quota_project_id=args.project)
    client = AsyncClient(project=args.project, database=args.database, credentials=credentials)
    root = client.collection("_smoke_tests").document(f"local-{uuid.uuid4().hex}")
    isolated = IsolatedClient(client, root)
    settings = Settings(
        _env_file=None,
        app_env="test",
        database_backend="firestore",
        payment_provider="mock",
        firestore_project_id=args.project,
        firestore_database_id=args.database,
        admin_emails=["admin@smoke.invalid"],
    )
    store = FirestoreStore(isolated, settings)  # type: ignore[arg-type]
    created = False
    deleted = 0
    checks: list[str] = []
    try:
        await root.create({"purpose": "local-backend-smoke", "created_at": now()})
        created = True
        identity = IdentityService(store)

        async def user(name: str) -> Any:
            return await identity.authenticate(
                {
                    "uid": f"{root.id}-{name}",
                    "email": f"{name}@smoke.invalid",
                    "name": f"Smoke {name}",
                    "email_verified": True,
                }
            )

        admin, interviewer, candidate = [
            await user(n) for n in ("admin", "interviewer", "candidate")
        ]
        checks.append("identity_storage")
        profiles = InterviewerService(store)
        profile = await profiles.create_profile(
            interviewer,
            ProfileUpsertRequest(
                title="Synthetic test interviewer",
                default_rate_minor=100,
                currency="INR",
            ),
        )
        await profiles.review_verification(
            profile.id, admin, VerificationReviewRequest(status="APPROVED")
        )
        interviewer = await user("interviewer")
        slot = await profiles.create_slot(
            interviewer,
            AvailabilitySlotCreateRequest(
                start_time=now() + timedelta(days=1),
                end_time=now() + timedelta(days=1, hours=1),
            ),
        )
        checks.append("profile_verification_and_availability")
        booking = await BookingService(store).reserve_slot(
            candidate, BookingReserveRequest(slot_id=slot["id"])
        )
        payment_service = PaymentService(store)
        await payment_service.create_checkout(candidate, booking.id, PaymentCheckoutRequest())
        payment = await store.reader().get("payments", booking.id)
        body = json.dumps(
            {
                "event_id": f"smoke-{root.id}",
                "booking_id": str(booking.id),
                "provider_payment_id": payment["provider_payment_id"],
                "amount_minor": 100,
                "currency": "INR",
                "status": "PAID",
            }
        ).encode()
        signature = MockPaymentProvider(settings.webhook_signing_secret).compute_signature(body)
        confirmed = await payment_service.process_webhook(
            "mock", body, {"x-webhook-signature": signature}
        )
        replay = await payment_service.process_webhook(
            "mock", body, {"x-webhook-signature": signature}
        )
        assert confirmed.status == "confirmed" and replay.status == "duplicate"
        checks.append("reservation_mock_payment_and_webhook_deduplication")
        rubrics = RubricService(store)
        await rubrics.submit_rubric(
            interviewer,
            booking.id,
            RubricSubmitRequest(
                technical_score=4,
                problem_solving_score=4,
                communication_score=4,
                detailed_feedback="Synthetic test feedback",
                private_interviewer_notes="private-smoke-note",
            ),
        )
        feedback = await rubrics.get_candidate_feedback(candidate, booking.id)
        assert "private-smoke-note" not in feedback.model_dump_json()
        reviews = ReviewService(store)
        await reviews.create_review(candidate, booking.id, ReviewCreateRequest(rating=4))
        assert (await reviews.get_interviewer_rating_summary(profile.id))["total_reviews"] == 1
        assert len(await reviews.list_interviewer_reviews(profile.id)) == 1
        checks.append("feedback_privacy_and_review_index")
        print(
            json.dumps({"checks_passed": checks, "database": args.database, "namespace": root.path})
        )
    finally:
        if created:
            for name in sorted(isolated.collections):
                while True:
                    docs = [doc async for doc in root.collection(name).limit(100).stream()]
                    if not docs:
                        break
                    batch = client.batch()
                    for doc in docs:
                        batch.delete(doc.reference)
                    await batch.commit()
                    deleted += len(docs)
            await root.delete()
            print(json.dumps({"cleanup": "complete", "test_documents_deleted": deleted + 1}))
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--database", required=True)
    parser.add_argument("--gcloud-credentials", action="store_true")
    parser.add_argument("--confirm-test-writes", action="store_true", required=True)
    args = parser.parse_args()
    asyncio.run(run(args))
