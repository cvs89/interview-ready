import asyncio
import hashlib
import hmac
import json
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import stripe
from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.models.booking import PaymentStatus


class WebhookSignatureVerificationError(Exception):
    pass


class PaymentCheckoutResult(BaseModel):
    checkout_session_id: str
    checkout_url: str
    provider_payment_id: str | None = None
    expires_at: datetime | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class WebhookEventResult(BaseModel):
    event_id: str
    event_type: str
    booking_id: uuid.UUID
    provider_payment_id: str | None = None
    amount_minor: int
    currency: str
    status: PaymentStatus
    payload: dict[str, Any] = Field(default_factory=dict)


class RefundResult(BaseModel):
    refund_id: str
    amount_minor: int
    currency: str
    status: str
    raw_response: dict[str, Any] = Field(default_factory=dict)


class PaymentProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name/slug of the payment provider."""
        ...

    @abstractmethod
    async def create_checkout(
        self,
        *,
        booking_id: uuid.UUID,
        candidate_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        success_url: str | None = None,
        cancel_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentCheckoutResult: ...

    @abstractmethod
    async def verify_webhook(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> WebhookEventResult: ...

    @abstractmethod
    async def refund(
        self,
        *,
        provider_payment_id: str,
        amount_minor: int,
        currency: str,
        reason: str | None = None,
    ) -> RefundResult: ...


class MockPaymentProvider(PaymentProvider):
    def __init__(self, secret: str = "local_dev_webhook_signing_secret") -> None:
        self.secret = secret

    @property
    def name(self) -> str:
        return "mock"

    async def create_checkout(
        self,
        *,
        booking_id: uuid.UUID,
        candidate_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        success_url: str | None = None,
        cancel_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentCheckoutResult:
        session_id = f"cs_test_{uuid.uuid4().hex}"
        payment_id = f"pi_test_{uuid.uuid4().hex}"
        checkout_url = f"https://checkout.interviewready.local/pay/{session_id}"
        return PaymentCheckoutResult(
            checkout_session_id=session_id,
            checkout_url=checkout_url,
            provider_payment_id=payment_id,
            raw_response={
                "booking_id": str(booking_id),
                "candidate_id": str(candidate_id),
                "amount_minor": amount_minor,
                "currency": currency,
            },
        )

    def compute_signature(self, payload_bytes: bytes) -> str:
        return hmac.new(self.secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    async def verify_webhook(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> WebhookEventResult:
        # Normalize header keys to lowercase
        norm_headers = {k.casefold(): v for k, v in headers.items()}
        signature = (
            norm_headers.get("x-webhook-signature")
            or norm_headers.get("stripe-signature")
            or norm_headers.get("signature")
        )
        if not signature:
            raise WebhookSignatureVerificationError("Missing webhook signature header.")

        expected_sig = self.compute_signature(payload_bytes)
        if not hmac.compare_digest(expected_sig, signature):
            raise WebhookSignatureVerificationError("Invalid webhook signature.")

        try:
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            raise WebhookSignatureVerificationError("Malformed webhook JSON payload.") from exc

        event_id = str(data.get("event_id") or data.get("id") or uuid.uuid4().hex)
        event_type = str(data.get("event_type") or data.get("type") or "payment.succeeded")

        raw_booking_id = data.get("booking_id")
        if not raw_booking_id and "metadata" in data and isinstance(data["metadata"], dict):
            raw_booking_id = data["metadata"].get("booking_id")
        if not raw_booking_id:
            raise WebhookSignatureVerificationError("Webhook payload missing 'booking_id'.")

        try:
            booking_id = uuid.UUID(str(raw_booking_id))
        except ValueError as exc:
            raise WebhookSignatureVerificationError("Invalid booking_id format.") from exc

        amount_minor = int(data.get("amount_minor", 0))
        currency = str(data.get("currency", "")).upper()
        provider_payment_id = data.get("provider_payment_id") or data.get("payment_id")

        raw_status = str(data.get("status", "PAID")).upper()
        if raw_status in PaymentStatus.__members__:
            status = PaymentStatus(raw_status)
        elif "SUCCEED" in raw_status or "PAID" in raw_status:
            status = PaymentStatus.PAID
        elif "FAIL" in raw_status:
            status = PaymentStatus.FAILED
        elif "CANCEL" in raw_status:
            status = PaymentStatus.CANCELLED
        else:
            status = PaymentStatus.PENDING

        return WebhookEventResult(
            event_id=event_id,
            event_type=event_type,
            booking_id=booking_id,
            provider_payment_id=provider_payment_id,
            amount_minor=amount_minor,
            currency=currency,
            status=status,
            payload=data,
        )

    async def refund(
        self,
        *,
        provider_payment_id: str,
        amount_minor: int,
        currency: str,
        reason: str | None = None,
    ) -> RefundResult:
        return RefundResult(
            refund_id=f"re_test_{uuid.uuid4().hex}",
            amount_minor=amount_minor,
            currency=currency,
            status="succeeded",
            raw_response={"provider_payment_id": provider_payment_id, "reason": reason},
        )


class StripePaymentProvider(PaymentProvider):
    def __init__(
        self,
        secret_key: str,
        webhook_secret: str | None = None,
    ) -> None:
        self.secret_key = secret_key
        self.webhook_secret = webhook_secret

    @property
    def name(self) -> str:
        return "stripe"

    async def create_checkout(
        self,
        *,
        booking_id: uuid.UUID,
        candidate_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        success_url: str | None = None,
        cancel_url: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PaymentCheckoutResult:
        meta = {
            "booking_id": str(booking_id),
            "candidate_id": str(candidate_id),
            **(metadata or {}),
        }
        fallback_success_url = f"https://interviewready.local/bookings/{booking_id}/confirmation"
        fallback_cancel_url = f"https://interviewready.local/bookings/{booking_id}"
        session_params: dict[str, Any] = {
            "mode": "payment",
            "payment_method_types": ["card"],
            "line_items": [
                {
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": "Interview Ready - Mock Interview Session",
                            "description": f"Session reservation {booking_id}",
                        },
                        "unit_amount": amount_minor,
                    },
                    "quantity": 1,
                }
            ],
            "client_reference_id": str(booking_id),
            "metadata": meta,
            "success_url": success_url or fallback_success_url,
            "cancel_url": cancel_url or fallback_cancel_url,
        }

        try:
            session = await asyncio.to_thread(
                stripe.checkout.Session.create,
                api_key=self.secret_key,
                **session_params,
            )
        except stripe.StripeError as exc:
            raise ApiError(
                "STRIPE_CHECKOUT_FAILED",
                f"Failed to create Stripe checkout session: {exc.user_message or str(exc)}",
                status_code=502,
            ) from exc

        session_id = str(getattr(session, "id", ""))
        checkout_url = str(getattr(session, "url", "") or "")
        payment_intent = getattr(session, "payment_intent", None)
        provider_payment_id = str(payment_intent) if payment_intent else None

        expires_at = None
        exp_timestamp = getattr(session, "expires_at", None)
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        raw_resp: dict[str, Any] = {}
        if hasattr(session, "to_dict") and callable(session.to_dict):
            val = session.to_dict()
            if isinstance(val, dict):
                raw_resp = val
        elif isinstance(session, dict):
            raw_resp = session

        return PaymentCheckoutResult(
            checkout_session_id=session_id,
            checkout_url=checkout_url,
            provider_payment_id=provider_payment_id,
            expires_at=expires_at,
            raw_response=raw_resp,
        )

    async def verify_webhook(
        self,
        payload_bytes: bytes,
        headers: dict[str, str],
    ) -> WebhookEventResult:
        norm_headers = {k.casefold(): v for k, v in headers.items()}
        sig_header = norm_headers.get("stripe-signature")
        if not sig_header:
            raise WebhookSignatureVerificationError("Missing 'stripe-signature' header.")
        if not self.webhook_secret:
            raise WebhookSignatureVerificationError("Stripe webhook secret is not configured.")

        try:
            event = stripe.Webhook.construct_event(
                payload_bytes,
                sig_header,
                self.webhook_secret,
            )
        except stripe.SignatureVerificationError as exc:
            raise WebhookSignatureVerificationError(
                f"Stripe signature verification failed: {exc}"
            ) from exc
        except Exception as exc:
            raise WebhookSignatureVerificationError(
                f"Stripe webhook payload parsing failed: {exc}"
            ) from exc

        event_dict: dict[str, Any] = (
            event.to_dict()
            if hasattr(event, "to_dict")
            else (dict(event) if isinstance(event, dict) else {})
        )

        event_id = str(event_dict.get("id") or uuid.uuid4().hex)
        event_type = str(event_dict.get("type") or "")

        data_obj: dict[str, Any] = event_dict.get("data", {}).get("object", {})

        # Extract booking_id
        client_ref = data_obj.get("client_reference_id")
        meta = data_obj.get("metadata") or {}
        if not isinstance(meta, dict):
            meta = {}

        raw_booking_id = client_ref or meta.get("booking_id")
        if not raw_booking_id:
            raw_booking_id = event_dict.get("booking_id")

        if not raw_booking_id:
            raise WebhookSignatureVerificationError("Stripe webhook payload missing 'booking_id'.")

        try:
            booking_id = uuid.UUID(str(raw_booking_id))
        except ValueError as exc:
            raise WebhookSignatureVerificationError(
                "Invalid booking_id format in Stripe webhook."
            ) from exc

        # Extract amount and currency
        amount_minor = (
            data_obj.get("amount_total")
            or data_obj.get("amount")
            or data_obj.get("amount_subtotal")
            or 0
        )
        currency = str(data_obj.get("currency") or "").upper()
        provider_payment_id = data_obj.get("payment_intent") or data_obj.get("id")

        # Map event type & payment status to PaymentStatus
        if event_type == "checkout.session.completed":
            payment_status_str = data_obj.get("payment_status")
            if payment_status_str == "paid":
                status = PaymentStatus.PAID
            elif payment_status_str in ("unpaid", "no_payment_required"):
                status = PaymentStatus.PENDING
            else:
                status = PaymentStatus.PENDING
        elif event_type in ("payment_intent.succeeded", "charge.succeeded"):
            status = PaymentStatus.PAID
        elif event_type in ("payment_intent.payment_failed", "charge.failed"):
            status = PaymentStatus.FAILED
        elif event_type in ("checkout.session.expired", "payment_intent.canceled"):
            status = PaymentStatus.CANCELLED
        elif event_type in ("charge.refunded",):
            status = PaymentStatus.REFUNDED
        else:
            status = PaymentStatus.PENDING

        return WebhookEventResult(
            event_id=event_id,
            event_type=event_type,
            booking_id=booking_id,
            provider_payment_id=str(provider_payment_id) if provider_payment_id else None,
            amount_minor=int(amount_minor),
            currency=currency,
            status=status,
            payload=event_dict,
        )

    async def refund(
        self,
        *,
        provider_payment_id: str,
        amount_minor: int,
        currency: str,
        reason: str | None = None,
    ) -> RefundResult:
        params: dict[str, Any] = {
            "amount": amount_minor,
            "api_key": self.secret_key,
        }
        if provider_payment_id.startswith("pi_"):
            params["payment_intent"] = provider_payment_id
        elif provider_payment_id.startswith("ch_"):
            params["charge"] = provider_payment_id
        else:
            params["payment_intent"] = provider_payment_id

        if reason in ("duplicate", "fraudulent", "requested_by_customer"):
            params["reason"] = reason

        try:
            refund_obj = await asyncio.to_thread(stripe.Refund.create, **params)
        except stripe.StripeError as exc:
            raise ApiError(
                "STRIPE_REFUND_FAILED",
                f"Failed to process Stripe refund: {exc.user_message or str(exc)}",
                status_code=502,
            ) from exc

        raw_resp: dict[str, Any] = {}
        if hasattr(refund_obj, "to_dict") and callable(refund_obj.to_dict):
            val = refund_obj.to_dict()
            if isinstance(val, dict):
                raw_resp = val
        elif isinstance(refund_obj, dict):
            raw_resp = refund_obj

        return RefundResult(
            refund_id=str(getattr(refund_obj, "id", "")),
            amount_minor=int(getattr(refund_obj, "amount", amount_minor)),
            currency=str(getattr(refund_obj, "currency", currency)).upper(),
            status=str(getattr(refund_obj, "status", "succeeded")),
            raw_response=raw_resp,
        )


def get_payment_provider(
    provider_name: str | None = None,
    settings: Settings | None = None,
) -> PaymentProvider:
    app_settings = settings or get_settings()
    name = (provider_name or app_settings.payment_provider).lower()
    if name in ("mock", "dev", "test"):
        return MockPaymentProvider(secret=app_settings.webhook_signing_secret)
    if name == "stripe":
        if not app_settings.stripe_secret_key:
            raise ValueError("STRIPE_SECRET_KEY is not configured in settings.")
        return StripePaymentProvider(
            secret_key=app_settings.stripe_secret_key,
            webhook_secret=app_settings.stripe_webhook_secret,
        )
    raise ValueError(f"Unsupported payment provider: '{name}'")
