import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_pool, close_pool
from backend.routes import webhooks, leaderboard, stats, health
from backend.services.stale_cleanup import close_stale_segments_periodically

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("tdwc-tracker")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_pool()
    logger.info("Database pool initialised")

    # Background task: close segments that have been open too long
    cleanup_task = asyncio.create_task(close_stale_segments_periodically())

    yield

    # Shutdown
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    await close_pool()
    logger.info("Database pool closed")


app = FastAPI(title="TDWC Zoom Tracker", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhooks.router)
app.include_router(leaderboard.router)
app.include_router(stats.router)
app.include_router(health.router)
