"""FastAPI application entry point."""

import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response as StarletteResponse

from src.api.routes import router
from src.config import (
    TEMP_CLEANUP_INTERVAL_SECONDS,
    TEMP_DIR,
    TEMP_TTL_SECONDS,
    validate_config,
)

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
    validate_config()
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("Temp directory: %s", TEMP_DIR)
    cleanup_task = asyncio.create_task(_cleanup_temp_files())
    yield
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass


class CSPMiddleware(BaseHTTPMiddleware):
    """Add Content-Security-Policy header to all responses."""

    async def dispatch(self, request: Request, call_next):
        response: StarletteResponse = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob:; "
            "font-src 'self'"
        )
        return response


app = FastAPI(title="Mosaic Coloring App", version="0.1.0", lifespan=lifespan)

# AC8: CORS middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# AC9: Content-Security-Policy header
app.add_middleware(CSPMiddleware)

app.include_router(router, prefix="/api")

static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
