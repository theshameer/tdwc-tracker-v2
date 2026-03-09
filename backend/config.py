import os

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is required")

ZOOM_WEBHOOK_SECRET = os.environ.get("ZOOM_WEBHOOK_SECRET")

# Day boundaries use this timezone (Europe/London = GMT/BST).
# All timestamps are stored as UTC; this is only used to decide
# which calendar date a session belongs to.
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "Europe/London")
