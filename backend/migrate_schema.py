"""
One-time migration script.

Run this against the Railway PostgreSQL database to:
1. Create the new tables (attendance_segments, user_identities, webhook_events)
2. Add indexes to the existing attendance table
3. Copy historical data from 'attendance' into 'attendance_segments'

Usage:
    DATABASE_URL=postgresql://... python -m backend.migrate_schema
"""

import asyncio
import os
import logging

import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migrate")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Set DATABASE_URL environment variable before running")

SCHEMA_SQL = """
-- =======================================================
-- New tables (safe to re-run: IF NOT EXISTS everywhere)
-- =======================================================

CREATE TABLE IF NOT EXISTS user_identities (
    id SERIAL PRIMARY KEY,
    canonical_email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS attendance_segments (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    user_name TEXT NOT NULL,
    participant_id TEXT,
    join_time TIMESTAMPTZ NOT NULL,
    leave_time TIMESTAMPTZ,
    duration_seconds INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT leave_after_join
        CHECK (leave_time IS NULL OR leave_time >= join_time),

    CONSTRAINT unique_join_event
        UNIQUE (session_id, user_email, join_time)
);

CREATE TABLE IF NOT EXISTS webhook_events (
    id BIGSERIAL PRIMARY KEY,
    event_type TEXT NOT NULL,
    zoom_event TEXT NOT NULL,
    session_id TEXT NOT NULL,
    user_email TEXT NOT NULL,
    participant_id TEXT,
    event_timestamp TIMESTAMPTZ NOT NULL,
    raw_payload JSONB,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT unique_webhook_event
        UNIQUE (event_type, session_id, user_email, event_timestamp)
);

-- =======================================================
-- Indexes on new tables
-- =======================================================

CREATE INDEX IF NOT EXISTS idx_segments_open
    ON attendance_segments (session_id, user_email)
    WHERE leave_time IS NULL;

CREATE INDEX IF NOT EXISTS idx_segments_join_time
    ON attendance_segments (join_time);

CREATE INDEX IF NOT EXISTS idx_segments_join_date
    ON attendance_segments ((join_time::date));

CREATE INDEX IF NOT EXISTS idx_segments_user_email
    ON attendance_segments (user_email);

CREATE INDEX IF NOT EXISTS idx_user_identities_email
    ON user_identities (canonical_email);

CREATE INDEX IF NOT EXISTS idx_webhook_events_dedup
    ON webhook_events (event_type, session_id, user_email, event_timestamp);

-- =======================================================
-- Indexes on the existing attendance table (improve legacy reads)
-- =======================================================

CREATE INDEX IF NOT EXISTS idx_attendance_session_id
    ON attendance (session_id);

CREATE INDEX IF NOT EXISTS idx_attendance_join_time
    ON attendance (join_time);

CREATE INDEX IF NOT EXISTS idx_attendance_email
    ON attendance (email);
"""


async def run_migration() -> None:
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # ---- Step 1: Create schema ----
        logger.info("Creating new tables and indexes...")
        await conn.execute(SCHEMA_SQL)
        logger.info("Schema created successfully.")

        # ---- Step 2: Count existing data ----
        old_count = await conn.fetchval(
            "SELECT COUNT(*) FROM attendance WHERE duration_minutes > 0"
        )
        logger.info(f"Found {old_count} completed rows in old 'attendance' table.")

        if old_count == 0:
            logger.info("Nothing to migrate.")
            return

        already_migrated = await conn.fetchval(
            "SELECT COUNT(*) FROM attendance_segments"
        )
        if already_migrated > 0:
            logger.info(
                f"attendance_segments already has {already_migrated} rows. "
                "Skipping data copy to avoid duplicates. "
                "Drop the table first if you want to re-migrate."
            )
            return

        # ---- Step 3: Copy data ----
        logger.info("Copying data from 'attendance' to 'attendance_segments'...")
        migrated = await conn.execute("""
            INSERT INTO attendance_segments
                (session_id, user_email, user_name, join_time, leave_time, duration_seconds)
            SELECT
                COALESCE(session_id, 'unknown'),
                CASE
                    WHEN email IS NOT NULL AND email != 'unknown' AND email != ''
                        THEN email
                    ELSE COALESCE(user_name, 'unknown')
                END,
                COALESCE(user_name, 'Anonymous'),
                join_time,
                leave_time,
                ROUND(duration_minutes * 60)::int
            FROM attendance
            WHERE duration_minutes > 0
              AND join_time IS NOT NULL
            ON CONFLICT (session_id, user_email, join_time) DO NOTHING
        """)
        logger.info(f"Data copy result: {migrated}")

        # ---- Step 4: Populate user_identities ----
        logger.info("Populating user_identities from migrated data...")
        await conn.execute("""
            INSERT INTO user_identities (canonical_email, display_name)
            SELECT DISTINCT ON (user_email)
                user_email,
                user_name
            FROM attendance_segments
            ORDER BY user_email, join_time DESC
            ON CONFLICT (canonical_email)
            DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = now()
        """)

        # ---- Step 5: Verify ----
        new_count = await conn.fetchval("SELECT COUNT(*) FROM attendance_segments")
        user_count = await conn.fetchval("SELECT COUNT(*) FROM user_identities")
        logger.info(
            f"Migration complete: {new_count} segments, {user_count} users. "
            f"(Old table had {old_count} completed rows.)"
        )

        old_total = await conn.fetchval(
            "SELECT ROUND(SUM(duration_minutes), 1) FROM attendance WHERE duration_minutes > 0"
        )
        new_total = await conn.fetchval(
            "SELECT ROUND(SUM(duration_seconds / 60.0), 1) FROM attendance_segments WHERE duration_seconds > 0"
        )
        logger.info(f"Duration check: old={old_total} min, new={new_total} min")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
