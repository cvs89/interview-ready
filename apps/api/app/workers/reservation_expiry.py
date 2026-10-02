import asyncio
import logging
from datetime import datetime
from typing import NoReturn

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.bookings import BookingService

logger = logging.getLogger(__name__)


async def expire_reservations_task(session: AsyncSession, now: datetime | None = None) -> int:
    service = BookingService(session)
    expired = await service.expire_stale_reservations(now=now)
    if expired > 0:
        logger.info("Expired %d stale slot reservations / pending bookings", expired)
    return expired


async def run_reservation_expiry_worker(
    session_factory: async_sessionmaker[AsyncSession],
    poll_interval_seconds: int = 60,
) -> NoReturn:
    logger.info(
        "Starting reservation expiry background worker (interval: %ds)", poll_interval_seconds
    )
    while True:
        try:
            async with session_factory() as session:
                await expire_reservations_task(session)
        except asyncio.CancelledError:
            logger.info("Reservation expiry worker cancelled.")
            raise
        except Exception as exc:
            logger.error("Error running reservation expiry task: %s", exc, exc_info=True)
        await asyncio.sleep(poll_interval_seconds)
