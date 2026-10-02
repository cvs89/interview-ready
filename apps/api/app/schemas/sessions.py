import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MintDesktopTicketRequest(BaseModel):
    booking_id: uuid.UUID


class MintDesktopTicketResponse(BaseModel):
    ticket: str
    expires_in_seconds: int
    join_closes_at: datetime
    booking_id: uuid.UUID


class ExchangeDesktopTicketRequest(BaseModel):
    ticket: str
    booking_id: uuid.UUID | None = None


class ExchangeDesktopTicketResponse(BaseModel):
    session_jwt: str
    livekit_url: str
    livekit_token: str
    room_name: str
    session_id: uuid.UUID
    booking_id: uuid.UUID
    role: str
    expires_in_seconds: int


class JoinStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: uuid.UUID
    can_join: bool
    server_time: datetime
    join_available_at: datetime
    join_closes_at: datetime
    reason: str | None = None
    room_name: str | None = None
