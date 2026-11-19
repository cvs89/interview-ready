import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.store import Document, FirestoreStore, UnitOfWork
from app.models.identity import User


def now() -> datetime:
    return datetime.now(UTC)


def new_doc(**fields: Any) -> Document:
    stamp = now()
    return {"id": str(uuid.uuid4()), "created_at": stamp, "updated_at": stamp, **fields}


def key_for(*parts: object) -> str:
    return hashlib.sha256("\x00".join(map(str, parts)).encode()).hexdigest()


def user_model(document: Document) -> User:
    return User(**{**document, "id": uuid.UUID(document["id"])})


def authorize(user: User, document: Document, *fields: str, admin: bool = True) -> None:
    if admin and user.role == "ADMIN":
        return
    if str(user.id) not in [document.get(field) for field in fields]:
        raise ApiError("FORBIDDEN", "You do not have permission for this resource.", 403)


def require_admin(user: User) -> None:
    if user.role != "ADMIN":
        raise ApiError("FORBIDDEN", "Administrator access is required.", 403)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: "[REDACTED]"
            if any(
                term in k.lower()
                for term in (
                    "token",
                    "ticket",
                    "secret",
                    "password",
                    "authorization",
                    "signature",
                    "card_number",
                    "cvv",
                )
            )
            else redact(v)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def audit(
    tx: UnitOfWork,
    event: str,
    resource: str,
    resource_id: object,
    actor: object = None,
    metadata: Document | None = None,
) -> None:
    doc = new_doc(
        event_type=event,
        resource_type=resource,
        resource_id=str(resource_id),
        actor_user_id=str(actor) if actor else None,
        request_id=None,
        metadata_json=redact(metadata or {}),
    )
    tx.put("audit", doc["id"], doc)


async def notify(
    tx: UnitOfWork,
    event: str,
    user_id: str,
    reference: str,
    title: str,
    body: str = "",
    data: Document | None = None,
    channels: list[str] | None = None,
) -> None:
    selected = {channel.upper() for channel in (channels or ["EMAIL", "IN_APP"])}
    if selected - {"EMAIL", "FCM", "IN_APP"}:
        raise ApiError("INVALID_CHANNEL", "Unsupported notification channel.", 422)
    key = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{event}:{user_id}:{reference}"))
    doc = new_doc(
        id=key,
        user_id=user_id,
        event_type=event,
        title=title,
        body=body,
        data={"reference_id": reference, **(data or {})},
        read_at=None,
    )
    if "IN_APP" in selected and not await tx.get("notifications", key):
        tx.put("notifications", key, doc)
    # Durable intent, not a claim that email/FCM have been delivered.
    for channel in sorted(selected - {"IN_APP"}):
        delivery_key = key_for(key, channel)
        if not await tx.get("notification_outbox", delivery_key):
            tx.put(
                "notification_outbox",
                delivery_key,
                new_doc(
                    id=delivery_key,
                    recipient_user_id=user_id,
                    event_type=event,
                    title=title,
                    body=body,
                    data=doc["data"],
                    status="PENDING",
                    channels=[channel],
                ),
            )


class BaseService:
    def __init__(self, store: FirestoreStore, settings: Any = None, **kwargs: Any) -> None:
        self.store = store
        self.settings = settings or store.settings

    async def scan(
        self, collection: str, filters: tuple[tuple[str, str, Any], ...] = ()
    ) -> list[Document]:
        """Bounded fallback for legacy offset/filter APIs, never silently truncate."""
        docs = await self.store.reader().query(
            collection, filters, limit=self.settings.firestore_scan_limit + 1
        )
        if len(docs) > self.settings.firestore_scan_limit:
            raise ApiError("QUERY_TOO_BROAD", "Narrow the query; scan budget exceeded.", 422)
        return docs
