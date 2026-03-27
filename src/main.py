"""FastAPI application entry point."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.config import TEMP_CLEANUP_INTERVAL_SECONDS, TEMP_DIR, TEMP_TTL_SECONDS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


async def _cleanup_temp_files() -> None:
    """Periodically delete temp directories older than TEMP_TTL_SECONDS."""
    import shutil

    while True:
        await asyncio.sleep(TEMP_CLEANUP_INTERVAL_SECONDS)
        try:
            now = time.time()
            count = 0
            for entry in TEMP_DIR.iterdir():
                if entry.is_dir() and (now - entry.stat().st_mtime) > TEMP_TTL_SECONDS:
                    shutil.rmtree(entry, ignore_errors=True)
                    count += 1
            if count:
                logger.info("Cleaned up %d expired temp directories", count)
        except Exception:
            logger.exception("Error during temp file cleanup")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create temp directory on startup; run cleanup task in background."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Temp directory: %s", TEMP_DIR)
    cleanup_task = asyncio.create_task(_cleanup_temp_files())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Mosaic Coloring App", version="0.1.0", lifespan=lifespan)
app.include_router(router, prefix="/api")

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
