import hashlib
import hmac
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.config import Settings, get_settings
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


def get_payment_provider(
    provider_name: str | None = None,
    settings: Settings | None = None,
) -> PaymentProvider:
    app_settings = settings or get_settings()
    name = (provider_name or app_settings.payment_provider).lower()
    if name in ("mock", "dev", "test"):
        return MockPaymentProvider(secret=app_settings.webhook_signing_secret)
    raise ValueError(f"Unsupported payment provider: '{name}'")
