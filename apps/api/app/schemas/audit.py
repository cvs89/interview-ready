import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    event_type: str
    resource_type: str
    resource_id: str
    request_id: str | None = None
    metadata: dict[str, Any] = Field(..., validation_alias="metadata_json")
    created_at: datetime
