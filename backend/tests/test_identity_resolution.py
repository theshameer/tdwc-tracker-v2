"""
Tests for identity resolution logic.

Verifies that when a user joins with no email, the system correctly
resolves their display name to a canonical email via the name_aliases table.

Run: TEST_DATABASE_URL=postgresql://shameer@localhost/tdwc_test python -m pytest backend/tests/ -v
"""

import asyncio
import os
import asyncpg
import pytest


# ---------------------------------------------------------------------------
# The resolution function (this is what webhooks.py will use)
# ---------------------------------------------------------------------------

async def resolve_email(conn: asyncpg.Connection, raw_email: str, user_name: str) -> str:
    """Resolve a user's canonical email from their raw webhook data.

    Priority:
    1. If raw_email is a real email, use it directly.
    2. Check name_aliases table for user_name → canonical_email.
    3. Check user_identities for display_name → canonical_email.
    4. Fall back to user_name as identifier.
    """
    if raw_email and raw_email.lower() not in ("unknown", "") and "@" in raw_email:
        return raw_email

    if user_name == "Anonymous":
        return user_name

    # Check aliases table first (handles multiple name variants)
    canonical = await conn.fetchval(
        "SELECT canonical_email FROM name_aliases WHERE display_name = $1",
        user_name,
    )
    if canonical:
        return canonical

    # Fallback: check user_identities (handles exact display_name match)
    canonical = await conn.fetchval(
        "SELECT canonical_email FROM user_identities WHERE display_name = $1 LIMIT 1",
        user_name,
    )
    if canonical:
        return canonical

    return user_name


# ---------------------------------------------------------------------------
# Test setup
# ---------------------------------------------------------------------------

DB_URL = os.environ.get("TEST_DATABASE_URL", "postgresql://shameer@localhost/tdwc_test")


def run(coro):
    """Helper to run async code in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def setup_db():
    conn = await asyncpg.connect(DB_URL)
    await conn.execute("DROP TABLE IF EXISTS name_aliases CASCADE")
    await conn.execute("DROP TABLE IF EXISTS user_identities CASCADE")

    await conn.execute("""
        CREATE TABLE user_identities (
            id SERIAL PRIMARY KEY,
            canonical_email TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    await conn.execute("""
        CREATE TABLE name_aliases (
            display_name TEXT PRIMARY KEY,
            canonical_email TEXT NOT NULL
        )
    """)

    await conn.execute("""
        INSERT INTO user_identities (canonical_email, display_name) VALUES
            ('business.shamalam@gmail.com', 'Shameer A'),
            ('zkhanmc7@gmail.com', 'Zaid Khan'),
            ('andyteapig@gmail.com', 'Andrew Allan')
    """)

    await conn.execute("""
        INSERT INTO name_aliases (display_name, canonical_email) VALUES
            ('Shameer A', 'business.shamalam@gmail.com'),
            ('Shameer', 'business.shamalam@gmail.com'),
            ('sham', 'business.shamalam@gmail.com'),
            ('Zaid Khan', 'zkhanmc7@gmail.com'),
            ('Andrew Allan', 'andyteapig@gmail.com'),
            ('andrew allan', 'andyteapig@gmail.com')
    """)

    return conn


async def teardown_db(conn):
    await conn.execute("DROP TABLE IF EXISTS name_aliases CASCADE")
    await conn.execute("DROP TABLE IF EXISTS user_identities CASCADE")
    await conn.close()


@pytest.fixture
def conn():
    c = run(setup_db())
    yield c
    run(teardown_db(c))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_real_email_passes_through(conn):
    """When a real email is provided, it should be used as-is."""
    result = run(resolve_email(conn, "zkhanmc7@gmail.com", "Zaid Khan"))
    assert result == "zkhanmc7@gmail.com"


def test_empty_email_resolves_via_alias(conn):
    """'sham' with no email should resolve to business.shamalam@gmail.com."""
    result = run(resolve_email(conn, "", "sham"))
    assert result == "business.shamalam@gmail.com"


def test_unknown_email_resolves_via_alias(conn):
    """'unknown' email with name 'Shameer' should resolve via alias."""
    result = run(resolve_email(conn, "unknown", "Shameer"))
    assert result == "business.shamalam@gmail.com"


def test_case_sensitive_aliases(conn):
    """Both 'andrew allan' and 'Andrew Allan' resolve to same email."""
    lower = run(resolve_email(conn, "", "andrew allan"))
    upper = run(resolve_email(conn, "", "Andrew Allan"))
    assert lower == "andyteapig@gmail.com"
    assert upper == "andyteapig@gmail.com"


def test_no_alias_falls_back_to_user_identities(conn):
    """If no alias exists, user_identities display_name lookup works."""
    run(conn.execute("DELETE FROM name_aliases WHERE display_name = 'Zaid Khan'"))
    result = run(resolve_email(conn, "", "Zaid Khan"))
    assert result == "zkhanmc7@gmail.com"  # found via user_identities


def test_completely_unknown_person_uses_name(conn):
    """A new person with no email and no alias gets their name as ID."""
    result = run(resolve_email(conn, "", "Brand New Person"))
    assert result == "Brand New Person"


def test_anonymous_stays_anonymous(conn):
    """Anonymous users should not be looked up."""
    result = run(resolve_email(conn, "", "Anonymous"))
    assert result == "Anonymous"


def test_multiple_aliases_same_email(conn):
    """All name variants for Shameer resolve to same email."""
    results = set()
    for name in ["Shameer A", "Shameer", "sham"]:
        results.add(run(resolve_email(conn, "", name)))
    assert results == {"business.shamalam@gmail.com"}


def test_name_as_email_field_resolves_via_alias(conn):
    """When Zoom sends the display name in the email field (no @), resolve via alias."""
    result = run(resolve_email(conn, "sham", "sham"))
    assert result == "business.shamalam@gmail.com"


def test_name_as_email_field_unknown_person(conn):
    """When Zoom sends a non-email string for an unknown person, fall back to name."""
    result = run(resolve_email(conn, "NewPerson", "NewPerson"))
    assert result == "NewPerson"
