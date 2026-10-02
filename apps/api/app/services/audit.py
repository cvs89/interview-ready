import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog
from app.models.identity import User, UserRole
from app.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogResponse

SENSITIVE_KEYS = {
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "password",
    "authorization",
    "card_number",
    "cvv",
    "signature",
}


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
    if not metadata:
        return {}
    sanitized: dict[str, Any] = {}
    for k, v in metadata.items():
        lower_k = k.lower()
        if any(secret_term in lower_k for secret_term in SENSITIVE_KEYS):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_metadata(v)
        else:
            sanitized[k] = v
    return sanitized


class AuditService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.audit_repo = AuditRepository(session)

    async def log_event(
        self,
        event_type: str,
        resource_type: str,
        resource_id: str,
        actor_user_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> AuditLog:
        clean_metadata = sanitize_metadata(metadata)
        audit_log = AuditLog(
            id=uuid.uuid4(),
            actor_user_id=actor_user_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            metadata_json=clean_metadata,
            created_at=datetime.now(UTC),
        )
        self.audit_repo.add(audit_log)
        await self.session.flush()
        return audit_log

    async def list_logs(
        self,
        user: User,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLogResponse]:
        if user.role != UserRole.ADMIN:
            actor_user_id = user.id

        logs = await self.audit_repo.list_logs(
            resource_type=resource_type,
            resource_id=resource_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            limit=limit,
            offset=offset,
        )
        return [AuditLogResponse.model_validate(log) for log in logs]
