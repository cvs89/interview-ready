import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InAppNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    event_type: str
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    read_at: datetime | None = None
    created_at: datetime


class NotificationEventPayload(BaseModel):
    event_type: str
    recipient_user_id: uuid.UUID
    title: str
    body: str
    data: dict[str, Any] = Field(default_factory=dict)
    reference_id: str | None = None
    channels: list[str] = Field(default_factory=lambda: ["EMAIL", "IN_APP"])


class TaskProcessRequest(BaseModel):
    task_type: str
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskProcessResponse(BaseModel):
    status: str = "COMPLETED"
    task_type: str
    processed_count: int = 0
    details: dict[str, Any] = Field(default_factory=dict)
