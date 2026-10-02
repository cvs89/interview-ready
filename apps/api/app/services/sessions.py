import secrets
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.integrations.redis import DesktopTicketStore
from app.integrations.tokens import create_livekit_token, create_session_jwt
from app.models.booking import BookingStatus
from app.models.identity import User, UserRole
from app.models.session import InterviewSession, SessionStatus
from app.repositories.bookings import BookingRepository
from app.repositories.sessions import InterviewSessionRepository
from app.schemas.sessions import (
    ExchangeDesktopTicketRequest,
    ExchangeDesktopTicketResponse,
    JoinStatusResponse,
    MintDesktopTicketRequest,
    MintDesktopTicketResponse,
)


class DesktopAuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.booking_repo = BookingRepository(session)
        self.session_repo = InterviewSessionRepository(session)

    def _compute_join_window(
        self, start_time: datetime, end_time: datetime
    ) -> tuple[datetime, datetime]:
        lead = timedelta(minutes=self.settings.join_window_lead_minutes)
        grace = timedelta(minutes=self.settings.join_window_grace_minutes)
        return start_time - lead, end_time + grace

    async def get_join_status(self, user: User, booking_id: uuid.UUID) -> JoinStatusResponse:
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.role != UserRole.ADMIN and user.id not in (
            booking.candidate_id,
            booking.interviewer_id,
        ):
            raise ApiError("FORBIDDEN", "You are not a participant in this interview.", 403)

        now = datetime.now(UTC)
        join_available_at, join_closes_at = self._compute_join_window(
            booking.slot.start_time, booking.slot.end_time
        )
        room_name = (
            booking.interview_session.livekit_room_name if booking.interview_session else None
        )

        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS):
            return JoinStatusResponse(
                booking_id=booking.id,
                can_join=False,
                server_time=now,
                join_available_at=join_available_at,
                join_closes_at=join_closes_at,
                reason=f"BOOKING_{booking.status.value}",
                room_name=room_name,
            )

        if now < join_available_at:
            return JoinStatusResponse(
                booking_id=booking.id,
                can_join=False,
                server_time=now,
                join_available_at=join_available_at,
                join_closes_at=join_closes_at,
                reason="JOIN_WINDOW_NOT_STARTED",
                room_name=room_name,
            )

        if now > join_closes_at:
            return JoinStatusResponse(
                booking_id=booking.id,
                can_join=False,
                server_time=now,
                join_available_at=join_available_at,
                join_closes_at=join_closes_at,
                reason="JOIN_WINDOW_CLOSED",
                room_name=room_name,
            )

        return JoinStatusResponse(
            booking_id=booking.id,
            can_join=True,
            server_time=now,
            join_available_at=join_available_at,
            join_closes_at=join_closes_at,
            reason="CAN_JOIN",
            room_name=room_name,
        )

    async def mint_desktop_ticket(
        self,
        user: User,
        request: MintDesktopTicketRequest,
        redis: Redis,
    ) -> MintDesktopTicketResponse:
        booking = await self.booking_repo.get_booking_by_id(request.booking_id)
        if booking is None:
            raise ApiError("BOOKING_NOT_FOUND", "Booking not found.", 404)

        if user.id == booking.candidate_id:
            role = "CANDIDATE"
        elif user.id == booking.interviewer_id:
            role = "INTERVIEWER"
        elif user.role == UserRole.ADMIN:
            role = "ADMIN"
        else:
            raise ApiError("FORBIDDEN", "You are not a participant in this interview.", 403)

        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.IN_PROGRESS):
            raise ApiError(
                "BOOKING_NOT_JOINABLE",
                f"Booking is in status '{booking.status.value}' and cannot be joined.",
                400,
            )

        now = datetime.now(UTC)
        join_available_at, join_closes_at = self._compute_join_window(
            booking.slot.start_time, booking.slot.end_time
        )

        if now < join_available_at:
            raise ApiError(
                "JOIN_WINDOW_NOT_STARTED",
                "The interview join window has not opened yet.",
                400,
            )

        if now > join_closes_at:
            raise ApiError(
                "JOIN_WINDOW_CLOSED",
                "The interview join window has closed.",
                400,
            )

        ticket = await DesktopTicketStore.mint_ticket(
            redis,
            user_id=user.id,
            booking_id=booking.id,
            role=role,
            ttl_seconds=self.settings.desktop_ticket_ttl_seconds,
        )

        return MintDesktopTicketResponse(
            ticket=ticket,
            expires_in_seconds=self.settings.desktop_ticket_ttl_seconds,
            join_closes_at=join_closes_at,
            booking_id=booking.id,
        )

    async def exchange_desktop_ticket(
        self,
        request: ExchangeDesktopTicketRequest,
        redis: Redis,
    ) -> ExchangeDesktopTicketResponse:
        ticket_data = await DesktopTicketStore.exchange_ticket(redis, request.ticket)
        if not ticket_data:
            raise ApiError(
                "INVALID_OR_EXPIRED_TICKET",
                "The desktop authentication ticket is invalid or has already been used.",
                401,
            )

        try:
            user_id = uuid.UUID(ticket_data["user_id"])
            ticket_booking_id = uuid.UUID(ticket_data["booking_id"])
            role = str(ticket_data["role"])
        except (KeyError, ValueError) as exc:
            raise ApiError(
                "INVALID_OR_EXPIRED_TICKET",
                "Ticket payload is corrupted.",
                401,
            ) from exc

        if request.booking_id is not None and request.booking_id != ticket_booking_id:
            raise ApiError(
                "BOOKING_MISMATCH",
                "Cross-check booking ID does not match ticket binding.",
                400,
            )

        booking = await self.booking_repo.get_booking_by_id_for_update(ticket_booking_id)
        if booking is None:
            raise ApiError("INVALID_OR_EXPIRED_TICKET", "Associated booking not found.", 401)

        user = await self.session.get(User, user_id)
        if user is None:
            raise ApiError("INVALID_OR_EXPIRED_TICKET", "Associated user not found.", 401)

        if booking.status in (
            BookingStatus.CANCELLED,
            BookingStatus.REFUNDED,
            BookingStatus.EXPIRED,
        ):
            raise ApiError(
                "BOOKING_NOT_JOINABLE",
                f"Booking is in '{booking.status.value}' status and cannot be joined.",
                400,
            )

        now = datetime.now(UTC)
        join_available_at, join_closes_at = self._compute_join_window(
            booking.slot.start_time, booking.slot.end_time
        )

        if now < join_available_at or now > join_closes_at:
            raise ApiError(
                "JOIN_WINDOW_CLOSED", "The interview join window is no longer active.", 400
            )

        # Get or create InterviewSession
        session_model = await self.session_repo.get_by_booking_id_for_update(booking.id)
        if session_model is None:
            # Cryptographically random room name (opaque, never predictable booking ID)
            room_name = f"room_{secrets.token_hex(16)}"
            session_model = InterviewSession(
                id=uuid.uuid4(),
                booking_id=booking.id,
                livekit_room_name=room_name,
                status=SessionStatus.READY,
            )
            self.session.add(session_model)
            await self.session.flush()

        # Update join timestamps
        if user.id == booking.candidate_id:
            session_model.candidate_joined_at = session_model.candidate_joined_at or now
        elif user.id == booking.interviewer_id:
            session_model.interviewer_joined_at = session_model.interviewer_joined_at or now

        # If both participants have joined, promote session to ACTIVE and booking to IN_PROGRESS
        if session_model.candidate_joined_at and session_model.interviewer_joined_at:
            session_model.status = SessionStatus.ACTIVE
            session_model.started_at = session_model.started_at or now
            if booking.status == BookingStatus.CONFIRMED:
                booking.status = BookingStatus.IN_PROGRESS
                booking.started_at = booking.started_at or now

        await self.session.commit()

        session_jwt = create_session_jwt(
            user=user,
            booking_id=booking.id,
            session_id=session_model.id,
            role=role,
            settings=self.settings,
        )
        livekit_token = create_livekit_token(
            user=user,
            room_name=session_model.livekit_room_name,
            booking_id=booking.id,
            role=role,
            settings=self.settings,
        )

        return ExchangeDesktopTicketResponse(
            session_jwt=session_jwt,
            livekit_url=self.settings.livekit_url,
            livekit_token=livekit_token,
            room_name=session_model.livekit_room_name,
            session_id=session_model.id,
            booking_id=booking.id,
            role=role,
            expires_in_seconds=self.settings.session_jwt_ttl_seconds,
        )
