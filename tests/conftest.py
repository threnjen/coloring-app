"""Shared test fixtures."""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.main import app
from src.models.mosaic import ColorPalette, GridCell, MosaicSheet


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_rgb_image() -> Image.Image:
    """A 200x150 test image with varied colors."""
    arr = np.zeros((150, 200, 3), dtype=np.uint8)
    # Red quadrant
    arr[:75, :100] = [200, 50, 50]
    # Green quadrant
    arr[:75, 100:] = [50, 180, 50]
    # Blue quadrant
    arr[75:, :100] = [50, 50, 200]
    # Yellow quadrant
    arr[75:, 100:] = [200, 200, 50]
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def low_contrast_image() -> Image.Image:
    """A 200x150 low-contrast grayscale-ish image."""
    arr = np.random.default_rng(42).integers(100, 150, size=(150, 200, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def small_image() -> Image.Image:
    """A tiny 30x30 image."""
    arr = np.random.default_rng(42).integers(0, 255, size=(30, 30, 3), dtype=np.uint8)
    return Image.fromarray(arr, "RGB")


@pytest.fixture
def transparent_png_image() -> Image.Image:
    """A 100x100 RGBA image with transparency."""
    arr = np.zeros((100, 100, 4), dtype=np.uint8)
    arr[:, :, 0] = 200  # Red
    arr[:, :, 3] = 128  # Semi-transparent
    return Image.fromarray(arr, "RGBA")


def make_jpeg_bytes(width: int = 400, height: int = 300) -> bytes:
    """Create a JPEG image in memory."""
    arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes(width: int = 400, height: int = 300, mode: str = "RGB") -> bytes:
    """Create a PNG image in memory."""
    if mode == "RGBA":
        arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 4), dtype=np.uint8)
    else:
        arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def upload_and_crop(client: TestClient, width: int = 800, height: int = 600) -> str:
    """Upload and crop an image, returning the cropped image ID."""
    data = make_jpeg_bytes(width, height)
    upload_res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
    assert upload_res.status_code == 200
    image_id = upload_res.json()["image_id"]

    crop_res = client.post(
        "/api/crop",
        json={"image_id": image_id, "x": 50, "y": 50, "width": 600, "height": 400},
    )
    assert crop_res.status_code == 200
    return crop_res.json()["cropped_image_id"]


def make_grid(n_colors: int, columns: int, rows: int) -> tuple[list[list[GridCell]], ColorPalette]:
    """Build a simple grid and palette for testing."""
    palette = ColorPalette(
        colors_rgb=np.random.default_rng(42).integers(0, 255, size=(n_colors, 3), dtype=np.uint8)
    )
    grid = []
    for r in range(rows):
        row_cells = []
        for c in range(columns):
            idx = (r * columns + c) % n_colors
            row_cells.append(GridCell(row=r, col=c, color_index=idx, label=palette.label(idx)))
        grid.append(row_cells)
    return grid, palette


def make_sheet(
    n_colors: int = 12,
    columns: int = 60,
    rows: int = 80,
    component_size_mm: float = 3.0,
    mode: str = "square",
) -> MosaicSheet:
    """Build a MosaicSheet for testing."""
    grid, palette = make_grid(n_colors, columns, rows)
    return MosaicSheet(
        mosaic_id="test-sheet",
        grid=grid,
        palette=palette,
        columns=columns,
        rows=rows,
        component_size_mm=component_size_mm,
        mode=mode,
    )


def mock_rembg_remove(image, **kwargs):
    """Deterministic mock for rembg.remove that produces a known RGBA output."""
    arr = np.array(image)
    h, w = arr.shape[:2]
    alpha = np.zeros((h, w), dtype=np.uint8)
    margin_h, margin_w = h // 5, w // 5
    alpha[margin_h : h - margin_h, margin_w : w - margin_w] = 255
    for i in range(margin_h):
        val = int(255 * i / margin_h)
        alpha[i, margin_w : w - margin_w] = val
        alpha[h - 1 - i, margin_w : w - margin_w] = val
    for j in range(margin_w):
        val = int(255 * j / margin_w)
        alpha[margin_h : h - margin_h, j] = val
        alpha[margin_h : h - margin_h, w - 1 - j] = val
    rgba = np.dstack([arr, alpha])
    return Image.fromarray(rgba, "RGBA")
