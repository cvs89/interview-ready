import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def add(self, log: AuditLog) -> AuditLog:
        self.session.add(log)
        return log

    async def list_logs(
        self,
        resource_type: str | None = None,
        resource_id: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        query = select(AuditLog)
        if resource_type is not None:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            query = query.where(AuditLog.resource_id == resource_id)
        if actor_user_id is not None:
            query = query.where(AuditLog.actor_user_id == actor_user_id)
        if event_type is not None:
            query = query.where(AuditLog.event_type == event_type)

        query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars())
