"""
Fix duplicate user identities in attendance_segments.

Some users joined with email on some sessions and without email on others.
When email was missing, the user_name was stored as user_email.
This script merges all name-based rows into the real email, and also
consolidates alternate emails for the same person.
"""

import asyncio
import os
import asyncpg

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")

# Each entry: (canonical_email, display_name, [old identifiers to merge into canonical])
MERGE_RULES = [
    # Shameer Ahamed — "Shameer A", "Shameer", "sham", and a second email
    (
        "business.shamalam@gmail.com",
        "Shameer A",
        ["Shameer A", "Shameer", "sham", "business.shamalam7@gmail.com"],
    ),
    # Zaid Khan
    (
        "zkhanmc7@gmail.com",
        "Zaid Khan",
        ["Zaid Khan"],
    ),
    # Andrew Allan — mixed case + name-only
    (
        "andyteapig@gmail.com",
        "Andrew Allan",
        ["Andrew Allan", "andrew allan"],
    ),
    # Dan M
    (
        "daniyalmahmood31@hotmail.com",
        "Dan M",
        ["Dan M"],
    ),
    # Zehra Shah
    (
        "zehrashah42@outlook.com",
        "Zehra Shah",
        ["Zehra Shah"],
    ),
    # Dec Leahy
    (
        "decleahy@icloud.com",
        "Dec Leahy",
        ["Dec Leahy"],
    ),
    # Avi Gupta
    (
        "avgpt06@gmail.com",
        "Avi",
        ["Avi"],
    ),
    # Zakiyah H — joins from iPhone without email
    (
        "Zakiyah's iPhone",
        "Zakiya H",
        ["Zakiyah H"],
    ),
]


async def main():
    if not DATABASE_URL:
        print("Set DATABASE_URL or DATABASE_PUBLIC_URL env var")
        return

    conn = await asyncpg.connect(DATABASE_URL)

    for canonical_email, display_name, old_ids in MERGE_RULES:
        print(f"\n=== {display_name} ({canonical_email}) ===")

        for old_id in old_ids:
            if old_id == canonical_email:
                continue

            count = await conn.fetchval(
                "SELECT COUNT(*) FROM attendance_segments WHERE user_email = $1",
                old_id,
            )
            if count == 0:
                print(f"  '{old_id}' → 0 segments (skip)")
                continue

            print(f"  '{old_id}' → {count} segments to merge")

            # Update attendance_segments
            result = await conn.execute(
                "UPDATE attendance_segments SET user_email = $1 WHERE user_email = $2",
                canonical_email,
                old_id,
            )
            print(f"    attendance_segments: {result}")

            # Update webhook_events
            result = await conn.execute(
                "UPDATE webhook_events SET user_email = $1 WHERE user_email = $2",
                canonical_email,
                old_id,
            )
            print(f"    webhook_events: {result}")

            # Remove stale user_identities row
            await conn.execute(
                "DELETE FROM user_identities WHERE canonical_email = $1",
                old_id,
            )

        # Upsert the canonical identity with the correct display name
        await conn.execute(
            """
            INSERT INTO user_identities (canonical_email, display_name)
            VALUES ($1, $2)
            ON CONFLICT (canonical_email)
            DO UPDATE SET display_name = $2, updated_at = now()
            """,
            canonical_email,
            display_name,
        )

    # Also update display names in attendance_segments to match
    print("\n=== Updating display names ===")
    for canonical_email, display_name, _ in MERGE_RULES:
        result = await conn.execute(
            "UPDATE attendance_segments SET user_name = $1 WHERE user_email = $2 AND user_name != $1",
            display_name,
            canonical_email,
        )
        affected = result.split()[-1]
        if affected != "0":
            print(f"  {canonical_email}: updated {affected} rows to display as '{display_name}'")

    # Verification
    print("\n=== Verification ===")
    rows = await conn.fetch("""
        SELECT user_email, user_name, COUNT(*) as segments,
               ROUND((SUM(COALESCE(duration_seconds,0))/60.0)::numeric, 0) as total_min
        FROM attendance_segments
        GROUP BY user_email, user_name
        ORDER BY total_min DESC
    """)
    for r in rows:
        print(f"  {r['user_name']:25s} {r['user_email']:40s} {r['segments']:4d} segments  {r['total_min']:>6} min")

    await conn.close()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
