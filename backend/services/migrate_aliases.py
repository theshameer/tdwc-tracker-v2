"""
One-time migration: create name_aliases table and populate it.

All operations are idempotent (IF NOT EXISTS, ON CONFLICT) so this is safe
to run on every startup. Once the table exists and is populated, the queries
are essentially no-ops.
"""

import logging

import asyncpg

logger = logging.getLogger("tdwc-tracker.migrate-aliases")

# (canonical_email, display_name, [ALL known name variants])
MERGE_RULES = [
    (
        "business.shamalam@gmail.com",
        "Shameer A",
        ["Shameer A", "Shameer", "sham", "business.shamalam7@gmail.com"],
    ),
    (
        "zkhanmc7@gmail.com",
        "Zaid Khan",
        ["Zaid Khan"],
    ),
    (
        "andyteapig@gmail.com",
        "Andrew Allan",
        ["Andrew Allan", "andrew allan"],
    ),
    (
        "daniyalmahmood31@hotmail.com",
        "Dan M",
        ["Dan M"],
    ),
    (
        "zehrashah42@outlook.com",
        "Zehra Shah",
        ["Zehra Shah"],
    ),
    (
        "decleahy@icloud.com",
        "Dec Leahy",
        ["Dec Leahy"],
    ),
    (
        "avgpt06@gmail.com",
        "Avi",
        ["Avi"],
    ),
    (
        "Zakiyah's iPhone",
        "Zakiya H",
        ["Zakiyah H", "Zakiyah's iPhone"],
    ),
    (
        "Nicole",
        "Nicole",
        ["Nicole"],
    ),
    (
        "Tim",
        "Tim",
        ["Tim"],
    ),
]


async def run_alias_migration(pool: asyncpg.Pool) -> None:
    """Create name_aliases table, merge duplicates, and populate aliases."""
    async with pool.acquire() as conn:
        # Step 1: Create table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS name_aliases (
                display_name TEXT PRIMARY KEY,
                canonical_email TEXT NOT NULL
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_name_aliases_email
                ON name_aliases (canonical_email)
        """)

        # Step 2: Merge old identifiers into canonical emails
        for canonical_email, display_name, aliases in MERGE_RULES:
            for old_id in aliases:
                if old_id == canonical_email:
                    continue

                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM attendance_segments WHERE user_email = $1",
                    old_id,
                )
                if count > 0:
                    logger.info("Merging '%s' (%d segments) → %s", old_id, count, canonical_email)
                    await conn.execute(
                        "UPDATE attendance_segments SET user_email = $1 WHERE user_email = $2",
                        canonical_email, old_id,
                    )
                    await conn.execute(
                        "UPDATE webhook_events SET user_email = $1 WHERE user_email = $2",
                        canonical_email, old_id,
                    )
                    await conn.execute(
                        "DELETE FROM user_identities WHERE canonical_email = $1",
                        old_id,
                    )

            # Consistent display names
            await conn.execute(
                "UPDATE attendance_segments SET user_name = $1 WHERE user_email = $2 AND user_name != $1",
                display_name, canonical_email,
            )

            # Upsert canonical identity
            await conn.execute(
                """
                INSERT INTO user_identities (canonical_email, display_name)
                VALUES ($1, $2)
                ON CONFLICT (canonical_email)
                DO UPDATE SET display_name = $2, updated_at = now()
                """,
                canonical_email, display_name,
            )

        # Step 3: Populate aliases
        alias_count = 0
        for canonical_email, _, aliases in MERGE_RULES:
            for alias in aliases:
                await conn.execute(
                    """
                    INSERT INTO name_aliases (display_name, canonical_email)
                    VALUES ($1, $2)
                    ON CONFLICT (display_name)
                    DO UPDATE SET canonical_email = $2
                    """,
                    alias, canonical_email,
                )
                alias_count += 1

        logger.info("Alias migration complete: %d aliases registered", alias_count)
