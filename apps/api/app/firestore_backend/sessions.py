import secrets
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.errors import ApiError
from app.firestore_backend.common import BaseService, authorize, new_doc, now, user_model
from app.firestore_backend.store import Document, UnitOfWork
from app.integrations.redis import DesktopTicketStore
from app.integrations.tokens import create_livekit_token, create_session_jwt
from app.schemas.sessions import (
    ExchangeDesktopTicketResponse,
    JoinStatusResponse,
    MintDesktopTicketResponse,
)


class DesktopAuthService(BaseService):
    def window(self, slot: Document) -> tuple[datetime, datetime]:
        return (
            slot["start_time"] - timedelta(minutes=self.settings.join_window_lead_minutes),
            slot["end_time"] + timedelta(minutes=self.settings.join_window_grace_minutes),
        )

    def role(self, user: Any, booking: Document) -> str:
        if str(user.id) == booking["candidate_id"]:
            return "CANDIDATE"
        if str(user.id) == booking["interviewer_id"]:
            return "INTERVIEWER"
        if user.role == "ADMIN":
            return "ADMIN"
        raise ApiError("FORBIDDEN", "Not an interview participant.", 403)

    def check_join(self, booking: Document, slot: Document) -> None:
        if booking["status"] not in ("CONFIRMED", "IN_PROGRESS"):
            raise ApiError("BOOKING_NOT_JOINABLE", "Booking is not joinable.", 400)
        opens, closes = self.window(slot)
        if now() < opens:
            raise ApiError("JOIN_WINDOW_NOT_STARTED", "Join window has not opened.", 400)
        if now() > closes:
            raise ApiError("JOIN_WINDOW_CLOSED", "Join window has closed.", 400)

    async def get_join_status(self, user: Any, booking_id: object) -> JoinStatusResponse:
        tx = self.store.reader()
        booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
        authorize(user, booking, "candidate_id", "interviewer_id")
        slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
        session = await tx.get("sessions", booking_id)
        reason = "CAN_JOIN"
        try:
            self.check_join(booking, slot)
        except ApiError as exc:
            reason = exc.code
        opens, closes = self.window(slot)
        return JoinStatusResponse(
            booking_id=booking_id,
            can_join=reason == "CAN_JOIN",
            server_time=now(),
            join_available_at=opens,
            join_closes_at=closes,
            reason=reason,
            room_name=(session or {}).get("livekit_room_name"),
        )

    async def mint_desktop_ticket(self, user: Any, request: Any, redis: Any) -> Any:
        tx = self.store.reader()
        booking = await tx.require("bookings", request.booking_id, "BOOKING_NOT_FOUND")
        role = self.role(user, booking)
        slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
        self.check_join(booking, slot)
        ticket = await DesktopTicketStore.mint_ticket(
            redis,
            user_id=user.id,
            booking_id=uuid.UUID(booking["id"]),
            role=role,
            ttl_seconds=self.settings.desktop_ticket_ttl_seconds,
        )
        return MintDesktopTicketResponse(
            ticket=ticket,
            booking_id=booking["id"],
            expires_in_seconds=self.settings.desktop_ticket_ttl_seconds,
            join_closes_at=self.window(slot)[1],
        )

    async def exchange_desktop_ticket(self, request: Any, redis: Any) -> Any:
        payload = await DesktopTicketStore.exchange_ticket(redis, request.ticket)
        if not payload:
            raise ApiError("INVALID_OR_EXPIRED_TICKET", "Ticket expired or already used.", 401)
        try:
            booking_id = str(uuid.UUID(payload["booking_id"]))
            user_id = str(uuid.UUID(payload["user_id"]))
        except (KeyError, ValueError, TypeError):
            raise ApiError("INVALID_OR_EXPIRED_TICKET", "Invalid ticket payload.", 401) from None
        if request.booking_id is not None and str(request.booking_id) != booking_id:
            raise ApiError("BOOKING_MISMATCH", "Ticket belongs to a different booking.", 400)

        async def operation(tx: UnitOfWork) -> tuple[Any, str, Document]:
            booking = await tx.require("bookings", booking_id, "BOOKING_NOT_FOUND")
            account = await tx.require("users", user_id, "USER_NOT_FOUND")
            if account["status"] != "ACTIVE":
                raise ApiError("ACCOUNT_DISABLED", "Account is not active.", 403)
            user = user_model(account)
            role = self.role(user, booking)
            if role != payload.get("role"):
                raise ApiError("FORBIDDEN", "Ticket role no longer valid.", 403)
            slot = await tx.require("slots", booking["slot_id"], "SLOT_NOT_FOUND")
            session = await tx.get("sessions", booking_id)
            self.check_join(booking, slot)
            if session and session["status"] == "ENDED":
                raise ApiError("SESSION_ENDED", "Interview has ended.", 400)
            session = session or new_doc(
                booking_id=booking_id,
                livekit_room_name=f"room_{secrets.token_hex(16)}",
                status="READY",
                candidate_joined_at=None,
                interviewer_joined_at=None,
                started_at=None,
                ended_at=None,
            )
            if role in ("CANDIDATE", "INTERVIEWER"):
                field = f"{role.lower()}_joined_at"
                session[field] = session[field] or now()
            if session["candidate_joined_at"] and session["interviewer_joined_at"]:
                session.update(status="ACTIVE", started_at=session["started_at"] or now())
                booking.update(status="IN_PROGRESS", started_at=booking["started_at"] or now())
                tx.put("bookings", booking_id, booking)
            tx.put("sessions", booking_id, session)
            return user, role, session

        user, role, session = await self.store.run(operation)
        return ExchangeDesktopTicketResponse(
            session_jwt=create_session_jwt(
                user=user,
                booking_id=uuid.UUID(booking_id),
                session_id=uuid.UUID(session["id"]),
                role=role,
                settings=self.settings,
            ),
            livekit_token=create_livekit_token(
                user=user,
                room_name=session["livekit_room_name"],
                booking_id=uuid.UUID(booking_id),
                role=role,
                settings=self.settings,
            ),
            livekit_url=self.settings.livekit_url,
            room_name=session["livekit_room_name"],
            session_id=session["id"],
            booking_id=booking_id,
            role=role,
            expires_in_seconds=self.settings.session_jwt_ttl_seconds,
        )
