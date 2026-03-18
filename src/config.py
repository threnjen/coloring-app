"""Configuration constants for the coloring app."""

import os
import tempfile
from pathlib import Path

# --- Upload ---
MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))
MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png"}
MAX_IMAGE_DIMENSION: int = int(os.getenv("MAX_IMAGE_DIMENSION", "4000"))
MIN_CROP_PIXELS: int = 50

# --- Color ---
MIN_COLORS: int = 8
MAX_COLORS: int = 20
LABEL_CHARS: str = "0123456789ABCDEFGHIJ"

# --- Grid (Phase 1: 4mm only) ---
COMPONENT_SIZE_MM: float = 4.0
GRID_COLUMNS: int = 50
GRID_ROWS: int = 65

# --- Paper: US Letter ---
PAPER_WIDTH_MM: float = 215.9
PAPER_HEIGHT_MM: float = 279.4
PRINTABLE_WIDTH_MM: float = 200.0
PRINTABLE_HEIGHT_MM: float = 263.5  # Top-margin reference; grid = GRID_ROWS * COMPONENT_SIZE_MM = 260mm (3.5mm extra bottom margin)
MARGIN_SIDE_MM: float = (PAPER_WIDTH_MM - PRINTABLE_WIDTH_MM) / 2
MARGIN_TOP_MM: float = (PAPER_HEIGHT_MM - PRINTABLE_HEIGHT_MM) / 2

# --- Temp storage ---
TEMP_DIR: Path = Path(os.getenv("COLORING_TEMP_DIR", tempfile.gettempdir())) / "coloring-app"
TEMP_TTL_SECONDS: int = int(os.getenv("TEMP_TTL_SECONDS", "3600"))
TEMP_CLEANUP_INTERVAL_SECONDS: int = int(os.getenv("TEMP_CLEANUP_INTERVAL_SECONDS", "300"))

# --- Enhancement ---
CONTRAST_FACTOR: float = float(os.getenv("CONTRAST_FACTOR", "1.3"))
SATURATION_FACTOR: float = float(os.getenv("SATURATION_FACTOR", "1.3"))
