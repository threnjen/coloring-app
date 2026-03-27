"""Configuration constants for the coloring app."""

import os
import tempfile
from pathlib import Path


def _parse_int_env(name: str, default: str) -> int:
    """Parse an integer environment variable with a clear error on failure."""
    raw = os.getenv(name, default)
    try:
        return int(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Environment variable {name}={raw!r} is not a valid integer"
        ) from exc


# --- Upload ---
MAX_UPLOAD_SIZE_MB: int = _parse_int_env("MAX_UPLOAD_SIZE_MB", "20")
MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png"}
MAX_IMAGE_DIMENSION: int = _parse_int_env("MAX_IMAGE_DIMENSION", "4000")
MIN_CROP_PIXELS: int = 50

# --- Color ---
MIN_COLORS: int = 8
MAX_COLORS: int = 20
LABEL_CHARS: str = "0123456789ABCDEFGHIJ"


# --- Grid (Phase 1 defaults: 3mm) ---
COMPONENT_SIZE_MM: float = 3.0
GRID_COLUMNS: int = 60
GRID_ROWS: int = 80

# Lookup table: (size_mm, mode) → (columns, rows)
GRID_DIMENSIONS: dict[tuple[int, str], tuple[int, int]] = {
    # Square
    (3, "square"): (60, 80),
    (4, "square"): (50, 65),
    (5, "square"): (40, 52),
    # Circle (same as square)
    (3, "circle"): (60, 80),
    (4, "circle"): (50, 65),
    (5, "circle"): (40, 52),
    # Hexagon (pointy-top)
    (3, "hexagon"): (60, 93),
    (4, "hexagon"): (45, 70),
    (5, "hexagon"): (36, 56),
}

# --- Paper: US Letter ---
PAPER_WIDTH_MM: float = 215.9
PAPER_HEIGHT_MM: float = 279.4
PRINTABLE_WIDTH_MM: float = (
    GRID_COLUMNS * COMPONENT_SIZE_MM
)  # Default 3mm: 180mm (margins vary by size/mode)
PRINTABLE_HEIGHT_MM: float = (
    GRID_ROWS * COMPONENT_SIZE_MM
)  # Default 3mm: 240mm (margins vary by size/mode)
MARGIN_SIDE_MM: float = (PAPER_WIDTH_MM - PRINTABLE_WIDTH_MM) / 2
MARGIN_TOP_MM: float = (PAPER_HEIGHT_MM - PRINTABLE_HEIGHT_MM) / 2

# --- Temp storage ---
TEMP_DIR: Path = (
    Path(os.getenv("COLORING_TEMP_DIR", tempfile.gettempdir())) / "coloring-app"
)
TEMP_TTL_SECONDS: int = _parse_int_env("TEMP_TTL_SECONDS", "3600")
TEMP_CLEANUP_INTERVAL_SECONDS: int = _parse_int_env(
    "TEMP_CLEANUP_INTERVAL_SECONDS", "300"
)


def validate_config() -> None:
    """Validate configuration at startup. Raises ValueError on problems."""
    if MAX_UPLOAD_SIZE_MB <= 0:
        raise ValueError("MAX_UPLOAD_SIZE_MB must be positive")
    if MAX_IMAGE_DIMENSION <= 0:
        raise ValueError("MAX_IMAGE_DIMENSION must be positive")
    if TEMP_TTL_SECONDS <= 0:
        raise ValueError("TEMP_TTL_SECONDS must be positive")
    if TEMP_CLEANUP_INTERVAL_SECONDS <= 0:
        raise ValueError("TEMP_CLEANUP_INTERVAL_SECONDS must be positive")
    # Verify TEMP_DIR parent is writable
    temp_parent = TEMP_DIR.parent
    if not temp_parent.exists():
        raise ValueError(f"TEMP_DIR parent does not exist: {temp_parent}")
    if not os.access(temp_parent, os.W_OK):
        raise ValueError(f"TEMP_DIR parent is not writable: {temp_parent}")
