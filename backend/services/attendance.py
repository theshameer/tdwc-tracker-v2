import json
import logging
from datetime import datetime

import asyncpg

logger = logging.getLogger("tdwc-tracker.attendance")


async def process_join_event(
    conn: asyncpg.Connection,
    session_id: str,
    email: str,
    user_name: str,
    participant_id: str | None,
    timestamp: datetime,
    raw_payload: dict,
) -> dict:
    """Record a participant joining the meeting.

    FIX BUG 8: The UNIQUE constraint (session_id, user_email, join_time)
    combined with ON CONFLICT DO NOTHING silently ignores duplicate
    webhook deliveries.
    """
    # Log the raw webhook for debugging / audit
    try:
        await conn.execute(
            """
            INSERT INTO webhook_events
                (event_type, zoom_event, session_id, user_email,
                 participant_id, event_timestamp, raw_payload)
            VALUES ('join', $1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (event_type, session_id, user_email, event_timestamp)
            DO NOTHING
            """,
            "meeting.participant_joined",
            session_id,
            email,
            participant_id,
            timestamp,
            json.dumps(raw_payload),
        )
    except Exception as exc:
        logger.warning("Failed to log webhook event: %s", exc)

    # Upsert user identity (keeps display_name up to date)
    if email and email != "unknown":
        await conn.execute(
            """
            INSERT INTO user_identities (canonical_email, display_name)
            VALUES ($1, $2)
            ON CONFLICT (canonical_email)
            DO UPDATE SET display_name = $2, updated_at = now()
            """,
            email,
            user_name,
        )

    # Insert the attendance segment (idempotent via unique constraint)
    result = await conn.execute(
        """
        INSERT INTO attendance_segments
            (session_id, user_email, user_name, participant_id, join_time)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (session_id, user_email, join_time) DO NOTHING
        """,
        session_id,
        email,
        user_name,
        participant_id,
        timestamp,
    )

    inserted = result.split()[-1] != "0"

    if inserted:
        logger.info("Segment opened: %s joined %s at %s", email, session_id, timestamp)
        return {"status": "success", "action": "segment_opened"}

    logger.info("Duplicate join ignored: %s / %s / %s", email, session_id, timestamp)
    return {"status": "success", "action": "duplicate_ignored"}


async def process_leave_event(
    conn: asyncpg.Connection,
    session_id: str,
    email: str,
    user_name: str,
    participant_id: str | None,
    timestamp: datetime,
    raw_payload: dict,
) -> dict:
    """Record a participant leaving the meeting.

    FIX BUG 2: We find the specific open segment by (session_id, user_email)
    then close it by its primary key `id`.  No more ambiguous OR matching.
    """
    # Log the raw webhook
    try:
        await conn.execute(
            """
            INSERT INTO webhook_events
                (event_type, zoom_event, session_id, user_email,
                 participant_id, event_timestamp, raw_payload)
            VALUES ('leave', $1, $2, $3, $4, $5, $6::jsonb)
            ON CONFLICT (event_type, session_id, user_email, event_timestamp)
            DO NOTHING
            """,
            "meeting.participant_left",
            session_id,
            email,
            participant_id,
            timestamp,
            json.dumps(raw_payload),
        )
    except Exception as exc:
        logger.warning("Failed to log webhook event: %s", exc)

    # Find the most recent open segment for this user in this session
    row = await conn.fetchrow(
        """
        SELECT id, join_time
        FROM attendance_segments
        WHERE session_id = $1
          AND user_email = $2
          AND leave_time IS NULL
        ORDER BY join_time DESC
        LIMIT 1
        """,
        session_id,
        email,
    )

    # Fallback: if email was 'unknown', try matching by participant_id
    if not row and email == "unknown" and participant_id:
        row = await conn.fetchrow(
            """
            SELECT id, join_time
            FROM attendance_segments
            WHERE session_id = $1
              AND participant_id = $2
              AND leave_time IS NULL
            ORDER BY join_time DESC
            LIMIT 1
            """,
            session_id,
            participant_id,
        )

    if not row:
        logger.warning(
            "No open segment for leave event: %s / %s", email, session_id
        )
        return {"status": "success", "action": "no_open_segment"}

    duration_sec = max(0, int((timestamp - row["join_time"]).total_seconds()))

    # Close the segment by primary key (safe, unambiguous)
    await conn.execute(
        """
        UPDATE attendance_segments
        SET leave_time = $1, duration_seconds = $2
        WHERE id = $3
        """,
        timestamp,
        duration_sec,
        row["id"],
    )

    logger.info(
        "Segment closed: %s left %s, duration=%ds", email, session_id, duration_sec
    )
    return {
        "status": "success",
        "action": "segment_closed",
        "duration_seconds": duration_sec,
    }
