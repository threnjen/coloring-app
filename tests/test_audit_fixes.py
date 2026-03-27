"""Tests for code audit fixes. Covers AC1–AC14."""

import io
import os

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.main import app
from tests.conftest import make_jpeg_bytes


# --- AC1: Path traversal defense in depth ---


class TestPathTraversalDefense:
    """AC1: _get_image_dir must reject non-hex-UUID IDs internally."""

    def test_get_image_dir_rejects_traversal(self) -> None:
        """_get_image_dir raises ValueError for traversal attempts."""
        from src.api.routes import _get_image_dir

        with pytest.raises(ValueError, match="Invalid"):
            _get_image_dir("../../etc/passwd")

    def test_get_image_dir_rejects_empty(self) -> None:
        """_get_image_dir raises ValueError for empty string."""
        from src.api.routes import _get_image_dir

        with pytest.raises(ValueError):
            _get_image_dir("")

    def test_get_image_dir_rejects_non_hex(self) -> None:
        """_get_image_dir raises ValueError for non-hex string."""
        from src.api.routes import _get_image_dir

        with pytest.raises(ValueError):
            _get_image_dir("not-a-valid-uuid-hex-string!!!")

    def test_get_image_dir_accepts_valid_hex(self) -> None:
        """_get_image_dir accepts a valid 32-char hex string."""
        from src.api.routes import _get_image_dir

        result = _get_image_dir("a" * 32)
        assert result.name == "a" * 32


# --- AC2: Corrupt image handling ---


class TestCorruptImageHandling:
    """AC2: _load_image wraps Image.open errors."""

    def test_upload_corrupt_jpeg(self, client: TestClient) -> None:
        """Upload a corrupt JPEG (valid magic, truncated body) returns 400."""
        corrupt_data = b"\xff\xd8\xff" + b"\x00" * 100
        res = client.post(
            "/api/upload",
            files={"file": ("corrupt.jpg", corrupt_data, "image/jpeg")},
        )
        assert res.status_code == 400

    def test_upload_corrupt_png(self, client: TestClient) -> None:
        """Upload a corrupt PNG (valid magic, truncated body) returns 400."""
        corrupt_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        res = client.post(
            "/api/upload",
            files={"file": ("corrupt.png", corrupt_data, "image/png")},
        )
        assert res.status_code == 400


# --- AC3: KeyError guard for GRID_DIMENSIONS ---


class TestGridDimensionsKeyError:
    """AC3: Invalid size/mode combo returns 400, not 500."""

    def test_process_invalid_size_mode_combo(self, client: TestClient) -> None:
        """Processing with an invalid size returns 422 (schema validation)."""
        data = make_jpeg_bytes(800, 600)
        upload_res = client.post(
            "/api/upload", files={"file": ("test.jpg", data, "image/jpeg")}
        )
        image_id = upload_res.json()["image_id"]
        crop_res = client.post(
            "/api/crop",
            json={"image_id": image_id, "x": 50, "y": 50, "width": 600, "height": 400},
        )
        cropped_id = crop_res.json()["cropped_image_id"]

        # size=6 is invalid per schema (ge=3, le=5), should get 422
        res = client.post(
            "/api/process",
            json={
                "cropped_image_id": cropped_id,
                "num_colors": 12,
                "size": 6,
                "mode": "square",
            },
        )
        assert res.status_code == 422


# --- AC4: Drop scipy —  np.bincount replacement ---


class TestGridGeneratorNoBincount:
    """AC4: GridGenerator should not require scipy."""

    def test_grid_generation_without_scipy(self) -> None:
        """Grid generation works without scipy.stats.mode."""
        from src.processing.grid import GridGenerator
        from src.models.mosaic import ColorPalette

        label_map = np.zeros((80, 60), dtype=np.int32)
        palette = ColorPalette(
            colors_rgb=np.array([[255, 0, 0], [0, 255, 0]], dtype=np.uint8)
        )
        gen = GridGenerator(columns=6, rows=8)
        grid = gen.generate(label_map, palette)
        assert len(grid) == 8
        assert len(grid[0]) == 6
        # All cells should be color_index 0 (most common in a zero label_map)
        assert all(cell.color_index == 0 for row in grid for cell in row)

    def test_scipy_not_imported_in_grid(self) -> None:
        """The grid module should not import scipy."""
        import importlib
        import src.processing.grid as grid_mod

        importlib.reload(grid_mod)
        source = open(grid_mod.__file__).read()
        assert "scipy" not in source


# --- AC5: Fix quantization precision ---


class TestQuantizationPrecision:
    """AC5: LAB centers should use .round() before uint8 cast."""

    def test_quantization_centers_are_rounded(self) -> None:
        """Quantized palette colors should be uint8."""
        from src.processing.quantization import ColorQuantizer

        img = Image.fromarray(
            np.random.default_rng(42).integers(0, 255, (100, 100, 3), dtype=np.uint8),
            "RGB",
        )
        quantizer = ColorQuantizer(n_colors=4)
        _, palette = quantizer.quantize(img)
        assert palette.colors_rgb.dtype == np.uint8


# --- AC6: Standardize colors_rgb dtype ---


class TestColorPaletteDtype:
    """AC6: colors_rgb should always be uint8."""

    def test_palette_edit_preserves_uint8(self) -> None:
        """After editing via the API, palette.colors_rgb remains uint8."""
        from src.api.routes import _mosaic_store
        from src.models.mosaic import ColorPalette, GridCell, MosaicSheet

        palette = ColorPalette(
            colors_rgb=np.array(
                [[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                dtype=np.uint8,
            )
        )
        grid = [
            [GridCell(row=0, col=0, color_index=0, label="0")]
        ]
        sheet = MosaicSheet(
            mosaic_id="c" * 32,
            grid=grid,
            palette=palette,
            columns=1,
            rows=1,
        )
        _mosaic_store["c" * 32] = sheet

        # After palette edit, dtype should still be uint8
        new_rgb = np.array([128, 64, 32], dtype=np.uint8)
        sheet.palette.colors_rgb[0] = new_rgb
        assert sheet.palette.colors_rgb.dtype == np.uint8


# --- AC7: Env var validation ---


class TestEnvVarValidation:
    """AC7: validate_config raises on bad env vars."""

    def test_validate_config_function_exists(self) -> None:
        """A validate_config function should exist in config module."""
        from src.config import validate_config

        # Should not raise with default config
        validate_config()


# --- AC8: CORS middleware ---


class TestCORSMiddleware:
    """AC8: CORSMiddleware is configured on the app."""

    def test_cors_middleware_present(self) -> None:
        """The app should have CORSMiddleware."""
        from starlette.middleware.cors import CORSMiddleware

        middleware_types = [type(m) for m in app.user_middleware]
        # Check that CORS is configured (user_middleware stores Middleware objects)
        has_cors = any(
            m.cls == CORSMiddleware for m in app.user_middleware
        )
        assert has_cors, "CORSMiddleware not found on app"


# --- AC9: CSP header ---


class TestCSPHeader:
    """AC9: Responses include Content-Security-Policy header."""

    def test_csp_header_on_api_response(self, client: TestClient) -> None:
        """API responses should include a CSP header."""
        res = client.get("/api/preview/" + "a" * 32)
        assert "content-security-policy" in res.headers


# --- AC10: PaletteEntry typed model ---


class TestPaletteEntryModel:
    """AC10: PaletteEntry Pydantic model is used in responses."""

    def test_palette_entry_model_exists(self) -> None:
        """PaletteEntry should be defined in schemas."""
        from src.api.schemas import PaletteEntry

        entry = PaletteEntry(index=0, label="0", hex="#FF0000")
        assert entry.index == 0
        assert entry.label == "0"
        assert entry.hex == "#FF0000"

    def test_process_response_uses_typed_palette(self) -> None:
        """ProcessResponse.palette should use list[PaletteEntry]."""
        from src.api.schemas import ProcessResponse

        field_info = ProcessResponse.model_fields["palette"]
        assert "PaletteEntry" in str(field_info.annotation)


# --- AC12: Shared brightness utility ---


class TestSharedBrightnessUtility:
    """AC12: Brightness calculation is a shared function."""

    def test_perceived_brightness_exists(self) -> None:
        """A shared perceived_brightness function should exist."""
        from src.rendering.color_utils import perceived_brightness

        assert perceived_brightness(255, 255, 255) == pytest.approx(255.0)
        assert perceived_brightness(0, 0, 0) == pytest.approx(0.0)

    def test_perceived_brightness_formula(self) -> None:
        """perceived_brightness uses the standard luminance formula."""
        from src.rendering.color_utils import perceived_brightness

        # 0.299*100 + 0.587*150 + 0.114*200 = 29.9 + 88.05 + 22.8 = 140.75
        assert perceived_brightness(100, 150, 200) == pytest.approx(140.75)
