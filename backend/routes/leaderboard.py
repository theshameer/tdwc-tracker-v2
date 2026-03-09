from datetime import date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query

from backend.config import APP_TIMEZONE
from backend.db import get_pool
from backend.services.aggregation import (
    get_daily_leaderboard,
    get_monthly_leaderboard,
    get_legacy_leaderboard,
)

router = APIRouter()


@router.get("/leaderboard/daily")
async def daily_leaderboard(
    date: date | None = Query(
        None, description="YYYY-MM-DD. Defaults to today in app timezone."
    ),
):
    """Pre-aggregated daily leaderboard (one row per user)."""
    target = date or datetime.now(ZoneInfo(APP_TIMEZONE)).date()
    pool = get_pool()
    async with pool.acquire() as conn:
        entries = await get_daily_leaderboard(conn, target, APP_TIMEZONE)
    return {"date": target.isoformat(), "timezone": APP_TIMEZONE, "entries": entries}


@router.get("/leaderboard/monthly")
async def monthly_leaderboard(
    month: str | None = Query(
        None, description="YYYY-MM. Defaults to current month in app timezone."
    ),
):
    """Pre-aggregated monthly leaderboard with performance scores."""
    if month:
        parts = month.split("-")
        target_year, target_month = int(parts[0]), int(parts[1])
    else:
        now = datetime.now(ZoneInfo(APP_TIMEZONE))
        target_year, target_month = now.year, now.month

    pool = get_pool()
    async with pool.acquire() as conn:
        entries = await get_monthly_leaderboard(
            conn, target_year, target_month, APP_TIMEZONE
        )
    return {
        "month": f"{target_year}-{target_month:02d}",
        "timezone": APP_TIMEZONE,
        "entries": entries,
    }


@router.get("/leaderboard")
async def legacy_leaderboard():
    """Legacy endpoint: individual segments in the old API format.

    Kept so the existing frontend continues to work during the transition.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        return await get_legacy_leaderboard(conn)
