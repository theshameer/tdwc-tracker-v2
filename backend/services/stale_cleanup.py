"""Background task that auto-closes attendance segments left open too long.

If Zoom fails to deliver a leave webhook (network issue, server crash, etc.)
the segment would stay open forever.  This task caps them at 12 hours.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from backend.db import get_pool

logger = logging.getLogger("tdwc-tracker.cleanup")

STALE_THRESHOLD_HOURS = 12
CLEANUP_INTERVAL_SECONDS = 3600  # run every hour


async def close_stale_segments() -> None:
    pool = get_pool()
    cutoff = datetime.now(timezone.utc) - timedelta(hours=STALE_THRESHOLD_HOURS)

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE attendance_segments
            SET leave_time  = join_time + interval '12 hours',
                duration_seconds = 12 * 3600
            WHERE leave_time IS NULL
              AND join_time < $1
            """,
            cutoff,
        )
        count = int(result.split()[-1])
        if count > 0:
            logger.info("Closed %d stale segments (open > %dh)", count, STALE_THRESHOLD_HOURS)


async def close_stale_segments_periodically() -> None:
    """Runs forever in a background asyncio task."""
    while True:
        try:
            await close_stale_segments()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error("Stale cleanup error: %s", exc)
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
