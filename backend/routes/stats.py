from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter

from backend.config import APP_TIMEZONE
from backend.db import get_pool
from backend.services.aggregation import get_today_stats

router = APIRouter()


@router.get("/stats/today")
async def today_stats():
    """Quick stats for dashboard header cards: total minutes + active members."""
    today = datetime.now(ZoneInfo(APP_TIMEZONE)).date()
    pool = get_pool()
    async with pool.acquire() as conn:
        return await get_today_stats(conn, today, APP_TIMEZONE)
