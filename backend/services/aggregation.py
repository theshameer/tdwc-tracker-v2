"""Server-side aggregation queries for leaderboards.

All date-boundary logic uses AT TIME ZONE so that a session at 23:30
London time counts for *that* calendar day, not the next UTC day.
"""

from datetime import date

import asyncpg


async def get_daily_leaderboard(
    conn: asyncpg.Connection,
    target_date: date,
    tz_name: str,
) -> list[dict]:
    """Aggregate attendance for a single calendar day.

    Returns one row per user, sorted by total time descending.
    """
    rows = await conn.fetch(
        """
        WITH day_segments AS (
            SELECT
                user_email,
                user_name,
                join_time,
                leave_time,
                duration_seconds
            FROM attendance_segments
            WHERE duration_seconds IS NOT NULL
              AND duration_seconds > 0
              AND (join_time AT TIME ZONE $2)::date = $1
        )
        SELECT
            user_email,
            (array_agg(user_name ORDER BY join_time DESC))[1] AS user_name,
            ROUND(SUM(duration_seconds) / 60.0, 1)            AS total_minutes,
            COUNT(*)                                           AS session_count,
            MIN(join_time)                                     AS first_join,
            MAX(leave_time)                                    AS last_leave
        FROM day_segments
        GROUP BY user_email
        ORDER BY SUM(duration_seconds) DESC
        """,
        target_date,
        tz_name,
    )

    return [
        {
            "user_email": r["user_email"],
            "user_name": r["user_name"],
            "total_minutes": float(r["total_minutes"]),
            "session_count": r["session_count"],
            "first_join": r["first_join"].isoformat() if r["first_join"] else None,
            "last_leave": r["last_leave"].isoformat() if r["last_leave"] else None,
        }
        for r in rows
    ]


async def get_monthly_leaderboard(
    conn: asyncpg.Connection,
    year: int,
    month: int,
    tz_name: str,
) -> list[dict]:
    """Aggregate attendance for a calendar month.

    Score = (total_hours * 0.7) + (unique_days * 0.3)
    """
    rows = await conn.fetch(
        """
        WITH month_segments AS (
            SELECT
                user_email,
                user_name,
                join_time,
                duration_seconds,
                (join_time AT TIME ZONE $3)::date AS local_date
            FROM attendance_segments
            WHERE duration_seconds IS NOT NULL
              AND duration_seconds > 0
              AND EXTRACT(YEAR  FROM (join_time AT TIME ZONE $3)) = $1
              AND EXTRACT(MONTH FROM (join_time AT TIME ZONE $3)) = $2
        )
        SELECT
            user_email,
            (array_agg(user_name ORDER BY join_time DESC))[1] AS user_name,
            ROUND(SUM(duration_seconds) / 60.0, 1)            AS total_minutes,
            COUNT(DISTINCT local_date)                         AS unique_days,
            COUNT(*)                                           AS session_count
        FROM month_segments
        GROUP BY user_email
        ORDER BY
            (SUM(duration_seconds) / 3600.0 * 0.7
             + COUNT(DISTINCT local_date) * 0.3) DESC
        """,
        year,
        month,
        tz_name,
    )

    return [
        {
            "user_email": r["user_email"],
            "user_name": r["user_name"],
            "total_minutes": float(r["total_minutes"]),
            "unique_days": r["unique_days"],
            "session_count": r["session_count"],
            "performance_score": round(
                float(r["total_minutes"]) / 60.0 * 0.7 + r["unique_days"] * 0.3,
                1,
            ),
        }
        for r in rows
    ]


async def get_today_stats(
    conn: asyncpg.Connection,
    today: date,
    tz_name: str,
) -> dict:
    """Quick aggregate for dashboard header cards."""
    row = await conn.fetchrow(
        """
        SELECT
            COALESCE(ROUND(SUM(duration_seconds) / 60.0, 1), 0) AS total_minutes,
            COUNT(DISTINCT user_email)                           AS active_members
        FROM attendance_segments
        WHERE duration_seconds IS NOT NULL
          AND duration_seconds > 0
          AND (join_time AT TIME ZONE $1)::date = $2
        """,
        tz_name,
        today,
    )

    return {
        "date": today.isoformat(),
        "total_minutes": float(row["total_minutes"]),
        "active_members": row["active_members"],
    }


async def get_legacy_leaderboard(conn: asyncpg.Connection) -> list[dict]:
    """Return individual segments in the old API shape.

    Kept for backward compatibility so the existing frontend keeps working
    while we deploy the new endpoints.
    """
    rows = await conn.fetch(
        """
        SELECT
            user_name,
            user_email AS email,
            join_time,
            leave_time,
            ROUND(duration_seconds / 60.0, 1) AS total_mins
        FROM attendance_segments
        WHERE duration_seconds IS NOT NULL
          AND duration_seconds > 0
        ORDER BY join_time DESC
        """
    )

    return [
        {
            "user_name": r["user_name"],
            "email": r["email"],
            "join_time": r["join_time"].isoformat() if r["join_time"] else None,
            "end_time": r["leave_time"].isoformat() if r["leave_time"] else None,
            "total_mins": float(r["total_mins"]),
        }
        for r in rows
    ]
