import hashlib
import hmac
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException

from backend.config import ZOOM_WEBHOOK_SECRET
from backend.db import get_pool
from backend.services.attendance import process_join_event, process_leave_event

router = APIRouter()
logger = logging.getLogger("tdwc-tracker.webhooks")


def parse_zoom_timestamp(value) -> datetime:
    """Convert whatever Zoom sends into a timezone-aware UTC datetime.

    Zoom can send:
      - ISO-8601 string  ("2026-03-09T10:30:00Z")
      - millisecond int  (1741513800000)
      - None             (fall back to server clock)
    """
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
    if isinstance(value, str):
        cleaned = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    return datetime.now(timezone.utc)


@router.post("/webhooks/zoom")
async def zoom_webhook(request: Request):
    data = await request.json()
    event = data.get("event")

    logger.info("Received Zoom event: %s", event)

    # ---- Zoom endpoint URL validation ----
    if event == "endpoint.url_validation":
        plain_token = data["payload"]["plainToken"]
        secret = ZOOM_WEBHOOK_SECRET
        if not secret:
            raise HTTPException(status_code=500, detail="Missing ZOOM_WEBHOOK_SECRET")
        encrypted = hmac.new(
            secret.encode(), plain_token.encode(), hashlib.sha256
        ).hexdigest()
        return {"plainToken": plain_token, "encryptedToken": encrypted}

    # Ignore anything that is not a join or leave
    if event not in ("meeting.participant_joined", "meeting.participant_left"):
        return {"status": "ignored", "event": event}

    # ---- Parse the Zoom payload ----
    obj = data.get("payload", {}).get("object", {}) or {}
    participant = obj.get("participant", {}) or {}

    # Session identifier: prefer uuid (unique per meeting instance)
    session_id = str(obj.get("uuid") or obj.get("id") or "unknown")

    # User identification — if no email, use name as the grouping key
    user_name = participant.get("user_name") or "Anonymous"
    email = participant.get("email") or ""
    if not email or email.lower() in ("unknown", ""):
        email = user_name
    participant_id = participant.get("user_id") or participant.get("id") or None

    # FIX BUG 1: Use Zoom's actual timestamp, not server time
    if event == "meeting.participant_joined":
        timestamp = parse_zoom_timestamp(
            participant.get("join_time") or data.get("event_ts")
        )
    else:
        timestamp = parse_zoom_timestamp(
            participant.get("leave_time") or data.get("event_ts")
        )

    pool = get_pool()

    # FIX BUG 6: async with guarantees connection release even on error
    async with pool.acquire() as conn:
        async with conn.transaction():
            if event == "meeting.participant_joined":
                result = await process_join_event(
                    conn, session_id, email, user_name,
                    participant_id, timestamp, data,
                )
            else:
                result = await process_leave_event(
                    conn, session_id, email, user_name,
                    participant_id, timestamp, data,
                )

    return result
