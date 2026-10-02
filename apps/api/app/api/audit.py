import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.core.rate_limit import RateLimiter
from app.db.session import get_session
from app.models.identity import User, UserRole
from app.schemas.audit import AuditLogResponse
from app.services.audit import AuditService

audit_router = APIRouter(prefix="/admin/audit-logs", tags=["admin-audit"])

Session = Annotated[AsyncSession, Depends(get_session)]
AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]


@audit_router.get(
    "",
    response_model=list[AuditLogResponse],
    dependencies=[Depends(RateLimiter(action="search_audit_logs", limit=60, window_seconds=60))],
)
async def list_audit_logs(
    _: AdminUser,
    session: Session,
    resource_type: str | None = None,
    resource_id: str | None = None,
    actor_user_id: uuid.UUID | None = None,
    event_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AuditLogResponse]:
    return await AuditService(session).list_logs(
        user=_,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_user_id=actor_user_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )
