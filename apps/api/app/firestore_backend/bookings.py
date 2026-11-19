import uuid
from datetime import timedelta
from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.common import (
    BaseService,
    audit,
    authorize,
    key_for,
    new_doc,
    notify,
    now,
)
from app.firestore_backend.store import Document, UnitOfWork
from app.integrations.payments import WebhookSignatureVerificationError, get_payment_provider
from app.schemas.bookings import BookingResponse, PaymentCheckoutResponse, WebhookEventResponse


async def release(tx: UnitOfWork, booking: Document, slot: Document, status: str) -> None:
    booking.update(status=status, updated_at=now())
    if slot.get("booking_id") == booking["id"]:
        slot.update(
            status="AVAILABLE",
            booking_id=None,
            reserved_by=None,
            reservation_expires_at=None,
            updated_at=now(),
        )
        tx.put("slots", slot["id"], slot)
    tx.put("bookings", booking["id"], booking)


class BookingService(BaseService):
    async def reserve_slot(self, user: Any, request: Any) -> BookingResponse:
        async def operation(tx: UnitOfWork) -> Document:
            slot = await tx.require("slots", request.slot_id, "SLOT_NOT_FOUND")
            profile = await tx.require("interviewers", slot["interviewer_id"], "PROFILE_NOT_FOUND")
            owner = await tx.require("users", profile["user_id"], "USER_NOT_FOUND")
            if profile["user_id"] == str(user.id):
                raise ApiError("CANNOT_BOOK_OWN_SLOT", "Cannot book your own slot.", 400)
            if not profile["is_verified"] or owner["status"] != "ACTIVE":
                raise ApiError("INTERVIEWER_NOT_APPROVED", "Interviewer is not available.", 400)
            stamp = now()
            if slot["start_time"] <= stamp:
                raise ApiError("SLOT_IN_PAST", "Slot is in the past.", 400)
            if slot["status"] == "RESERVED" and slot["reservation_expires_at"] <= stamp:
                old = await tx.require("bookings", slot["booking_id"], "BOOKING_NOT_FOUND")
                if old["status"] != "PENDING_PAYMENT":
                    raise ApiError("SLOT_UNAVAILABLE", "Slot needs reconciliation.", 409)
                await release(tx, old, slot, "EXPIRED")
            if slot["status"] != "AVAILABLE":
                code = {"RESERVED": "SLOT_ALREADY_RESERVED", "BOOKED": "SLOT_ALREADY_BOOKED"}
                raise ApiError(
                    code.get(slot["status"], "SLOT_UNAVAILABLE"), "Slot unavailable.", 409
                )
            expires = stamp + timedelta(minutes=self.settings.reservation_ttl_minutes)
            booking = new_doc(
                slot_id=slot["id"],
                candidate_id=str(user.id),
                interviewer_id=profile["user_id"],
                status="PENDING_PAYMENT",
                price_minor=slot["price_minor"],
                currency=slot["currency"],
                reservation_expires_at=expires,
                confirmed_at=None,
                started_at=None,
                completed_at=None,
                cancelled_at=None,
                cancellation_reason=None,
            )
            slot.update(
                status="RESERVED",
                booking_id=booking["id"],
                reserved_by=str(user.id),
                reservation_expires_at=expires,
            )
            tx.put("slots", slot["id"], slot)
            tx.put("bookings", booking["id"], booking)
            audit(tx, "BOOKING_RESERVED", "BOOKING", booking["id"], user.id)
            return booking

        return BookingResponse.model_validate(await self.store.run(operation))

    async def get_booking(self, user: Any, booking_id: object) -> BookingResponse:
        doc = await self.store.reader().require("bookings", booking_id, "BOOKING_NOT_FOUND")
        authorize(user, doc, "candidate_id", "interviewer_id")
        return BookingResponse.model_validate(doc)

    async def list_user_bookings(self, user: Any) -> list[BookingResponse]:
        field = "interviewer_id" if user.role == "INTERVIEWER" else "candidate_id"
        docs = await self.scan("bookings", ((field, "==", str(user.id)),))
        return [
            BookingResponse.model_validate(d)
            for d in sorted(docs, key=lambda d: d["created_at"], reverse=True)
        ]

    async def cancel_booking(
        self, user: Any, booking_id: object, reason: str | None = None
    ) -> BookingResponse:
        async def operation(tx: UnitOfWork) -> Document:
            booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
            authorize(user, booking, "candidate_id", "interviewer_id")
            slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
            payment = await tx.get("payments", booking_id)
            if booking["status"] not in ("PENDING_PAYMENT", "CONFIRMED"):
                raise ApiError("BOOKING_NOT_CANCELLABLE", "Booking cannot be cancelled.", 409)
            booking.update(cancelled_at=now(), cancellation_reason=reason)
            await release(tx, booking, slot, "CANCELLED")
            if payment and payment["status"] == "PAID":
                queue_refund(tx, payment, "booking_cancelled")
            audit(tx, "BOOKING_CANCELLED", "BOOKING", booking_id, user.id)
            await notify(
                tx,
                "BOOKING_CANCELLED",
                booking["candidate_id"],
                str(booking_id),
                "Interview cancelled",
                data={"booking_id": str(booking_id)},
            )
            return booking

        return BookingResponse.model_validate(await self.store.run(operation))

    async def expire_stale_reservations(self) -> int:
        # Bounded batch: repeated invocations drain the queue without full scans.
        slots = await self.store.reader().query(
            "slots",
            (
                ("status", "==", "RESERVED"),
                ("reservation_expires_at", "<=", now()),
            ),
            limit=100,
        )
        count = 0
        for snapshot in slots:

            async def operation(tx: UnitOfWork, snapshot: Document = snapshot) -> int:
                slot = await tx.require("slots", snapshot["id"], "SLOT_NOT_FOUND")
                if slot["status"] != "RESERVED" or slot["reservation_expires_at"] > now():
                    return 0
                booking = await tx.require("bookings", slot["booking_id"], "BOOKING_NOT_FOUND")
                if booking["status"] != "PENDING_PAYMENT":
                    return 0
                await release(tx, booking, slot, "EXPIRED")
                audit(tx, "RESERVATION_EXPIRED", "BOOKING", booking["id"])
                return 1

            count += await self.store.run(operation)
        return count


def queue_refund(tx: UnitOfWork, payment: Document, reason: str) -> None:
    tx.put(
        "refund_jobs",
        payment["id"],
        new_doc(
            id=payment["id"],
            booking_id=payment["booking_id"],
            status="PENDING",
            provider=payment["provider"],
            provider_payment_id=payment.get("provider_payment_id"),
            amount_minor=payment["amount_minor"],
            currency=payment["currency"],
            reason=reason,
            idempotency_key=f"refund:{payment['id']}",
        ),
    )


class PaymentService(BaseService):
    def provider(self, name: str | None) -> Any:
        configured = self.settings.payment_provider
        if name and name != configured:
            raise ApiError("PAYMENT_PROVIDER_DISABLED", "Payment provider is not enabled.", 400)
        if self.settings.app_env == "production" and configured != "stripe":
            raise ApiError(
                "PAYMENT_PROVIDER_DISABLED", "Production payment provider required.", 503
            )
        return get_payment_provider(configured, self.settings)

    async def create_checkout(
        self, user: Any, booking_id: object, request: Any, provider_name: str | None = None
    ) -> PaymentCheckoutResponse:
        provider = self.provider(provider_name)

        async def prepare(tx: UnitOfWork) -> Document:
            booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
            authorize(user, booking, "candidate_id", admin=False)
            slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
            payment = await tx.get("payments", booking_id)
            if (
                booking["status"] != "PENDING_PAYMENT"
                or slot.get("booking_id") != str(booking_id)
                or slot["status"] != "RESERVED"
                or slot["reservation_expires_at"] <= now()
            ):
                raise ApiError("RESERVATION_EXPIRED", "Reservation is no longer payable.", 409)
            if payment is None:
                payment = new_doc(
                    booking_id=str(booking_id),
                    candidate_id=str(user.id),
                    provider=provider.name,
                    amount_minor=booking["price_minor"],
                    currency=booking["currency"],
                    status="PENDING",
                    provider_payment_id=None,
                    provider_checkout_session_id=None,
                    checkout_url=None,
                    expires_at=None,
                    paid_at=None,
                    refunded_at=None,
                    success_url=request.success_url,
                    cancel_url=request.cancel_url,
                )
                tx.put("payments", booking_id, payment)
            return payment

        payment = await self.store.run(prepare)
        if not payment.get("checkout_url"):
            # External I/O is outside the transaction; a persisted stable payment
            # ID is the provider idempotency key across retries/process crashes.
            result = await provider.create_checkout(
                booking_id=uuid.UUID(str(booking_id)),
                candidate_id=user.id,
                amount_minor=payment["amount_minor"],
                currency=payment["currency"],
                success_url=payment["success_url"],
                cancel_url=payment["cancel_url"],
                metadata={"checkout_idempotency_key": f"checkout:{payment['id']}"},
            )

            async def finish(tx: UnitOfWork) -> Document:
                current = await tx.require("payments", booking_id, "PAYMENT_NOT_FOUND")
                current.update(
                    checkout_url=result.checkout_url,
                    provider_checkout_session_id=result.checkout_session_id,
                    expires_at=result.expires_at,
                    updated_at=now(),
                )
                if not current.get("provider_payment_id"):
                    current["provider_payment_id"] = result.provider_payment_id
                tx.put("payments", booking_id, current)
                return current

            payment = await self.store.run(finish)
        return PaymentCheckoutResponse.model_validate({**payment, "payment_id": payment["id"]})

    async def process_webhook(
        self, provider_name: str, payload_bytes: bytes, headers: dict[str, str]
    ) -> WebhookEventResponse:
        provider = self.provider(provider_name)
        try:
            event = await provider.verify_webhook(payload_bytes, headers)
        except WebhookSignatureVerificationError:
            raise ApiError("INVALID_WEBHOOK_SIGNATURE", "Invalid payment webhook.", 400) from None
        event_key = key_for(provider.name, event.event_id)

        async def operation(tx: UnitOfWork) -> str:
            if await tx.get("payment_events", event_key):
                return "duplicate"
            booking = await tx.require("bookings", event.booking_id, "BOOKING_NOT_FOUND")
            payment = await tx.require("payments", event.booking_id, "PAYMENT_NOT_FOUND")
            slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
            if (
                payment["provider"] != provider.name
                or event.amount_minor != payment["amount_minor"]
                or event.currency != payment["currency"]
            ):
                raise ApiError("PAYMENT_MISMATCH", "Payment does not match booking.", 400)
            if (
                payment.get("provider_payment_id")
                and event.provider_payment_id
                and payment["provider_payment_id"] != event.provider_payment_id
            ):
                raise ApiError("PAYMENT_MISMATCH", "Payment identifier does not match.", 400)
            if event.provider_payment_id:
                payment_key = key_for(provider.name, event.provider_payment_id)
                binding = await tx.get("payment_keys", payment_key)
                if binding and binding["booking_id"] != booking["id"]:
                    raise ApiError("PAYMENT_MISMATCH", "Payment already belongs to a booking.", 409)
                tx.put("payment_keys", payment_key, {"booking_id": booking["id"]})
                payment["provider_payment_id"] = event.provider_payment_id
            outcome = "ignored"
            if event.status == "PAID" and payment["status"] not in ("PAID", "REFUNDED"):
                payment.update(status="PAID", paid_at=now())
                valid = (
                    booking["status"] == "PENDING_PAYMENT"
                    and slot.get("booking_id") == booking["id"]
                    and slot["status"] == "RESERVED"
                    and slot["reservation_expires_at"] > now()
                )
                if valid:
                    booking.update(
                        status="CONFIRMED", confirmed_at=now(), reservation_expires_at=None
                    )
                    slot.update(status="BOOKED", reservation_expires_at=None, reserved_by=None)
                    tx.put("bookings", booking["id"], booking)
                    tx.put("slots", slot["id"], slot)
                    for recipient in (booking["candidate_id"], booking["interviewer_id"]):
                        await notify(
                            tx,
                            "BOOKING_CONFIRMED",
                            recipient,
                            booking["id"],
                            "Interview confirmed",
                            data={"booking_id": booking["id"]},
                        )
                    outcome = "confirmed"
                else:
                    if booking["status"] == "PENDING_PAYMENT":
                        await release(tx, booking, slot, "EXPIRED")
                    queue_refund(tx, payment, "late_payment")
                    outcome = "refund_pending"
            elif event.status in ("FAILED", "CANCELLED") and payment["status"] == "PENDING":
                payment["status"] = str(event.status)
                if booking["status"] == "PENDING_PAYMENT":
                    await release(tx, booking, slot, "EXPIRED")
                outcome = f"payment_{str(event.status).lower()}"
            elif event.status == "REFUNDED" and payment["status"] == "PAID":
                payment.update(status="REFUNDED", refunded_at=now())
                await release(tx, booking, slot, "REFUNDED")
                job = await tx.get("refund_jobs", payment["id"])
                if job:
                    tx.put("refund_jobs", payment["id"], {**job, "status": "COMPLETED"})
                outcome = "refunded"
            payment["updated_at"] = now()
            tx.put("payments", booking["id"], payment)
            tx.put(
                "payment_events",
                event_key,
                new_doc(
                    provider=provider.name,
                    event_id=event.event_id,
                    booking_id=booking["id"],
                    outcome=outcome,
                    processed_at=now(),
                ),
            )
            audit(
                tx,
                "PAYMENT_EVENT_PROCESSED",
                "PAYMENT",
                payment["id"],
                metadata={"outcome": outcome, "booking_id": booking["id"]},
            )
            return outcome

        return WebhookEventResponse(status=await self.store.run(operation))
