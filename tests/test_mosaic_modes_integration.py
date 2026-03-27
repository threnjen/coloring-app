"""Integration tests for mosaic mode pipeline. AC2.1, AC2.8."""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


def _make_jpeg_bytes(width: int = 400, height: int = 300) -> bytes:
    """Create a JPEG image in memory."""
    arr = np.random.default_rng(42).integers(
        0, 255, size=(height, width, 3), dtype=np.uint8
    )
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _upload_and_crop(client: TestClient) -> str:
    """Upload and crop an image, returning the cropped image ID."""
    data = _make_jpeg_bytes(800, 600)
    upload_res = client.post(
        "/api/upload", files={"file": ("test.jpg", data, "image/jpeg")}
    )
    assert upload_res.status_code == 200
    image_id = upload_res.json()["image_id"]

    crop_res = client.post(
        "/api/crop",
        json={"image_id": image_id, "x": 50, "y": 50, "width": 600, "height": 400},
    )
    assert crop_res.status_code == 200
    return crop_res.json()["cropped_image_id"]


class TestPipelineCircleMode:
    """Integration tests for circle mode pipeline."""

    def test_pipeline_circle_mode(self, client: TestClient) -> None:
        """Full pipeline with mode=circle produces valid PDF."""
        cropped_id = _upload_and_crop(client)

        process_res = client.post(
            "/api/process",
            json={
                "cropped_image_id": cropped_id,
                "num_colors": 12,
                "size": 3,
                "mode": "circle",
            },
        )
        assert process_res.status_code == 200
        body = process_res.json()
        assert body["mode"] == "circle"
        mosaic_id = body["mosaic_id"]

        # Preview should work
        preview_res = client.get(f"/api/preview/{mosaic_id}")
        assert preview_res.status_code == 200

        # PDF should work
        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
        assert pdf_res.content[:5] == b"%PDF-"


class TestPipelineHexagonMode:
    """Integration tests for hexagon mode pipeline."""

    def test_pipeline_hexagon_mode(self, client: TestClient) -> None:
        """Full pipeline with mode=hexagon produces valid PDF."""
        cropped_id = _upload_and_crop(client)

        process_res = client.post(
            "/api/process",
            json={
                "cropped_image_id": cropped_id,
                "num_colors": 12,
                "size": 3,
                "mode": "hexagon",
            },
        )
        assert process_res.status_code == 200
        body = process_res.json()
        assert body["mode"] == "hexagon"
        mosaic_id = body["mosaic_id"]

        # Preview should work
        preview_res = client.get(f"/api/preview/{mosaic_id}")
        assert preview_res.status_code == 200

        # PDF should work
        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
        assert pdf_res.content[:5] == b"%PDF-"


class TestModeSwitchPreservesPalette:
    """Test that switching mode preserves palette."""

    def test_mode_switch_preserves_palette(self, client: TestClient) -> None:
        """Process as square, then as circle — same palette colors and order."""
        cropped_id = _upload_and_crop(client)

        sq_res = client.post(
            "/api/process",
            json={
                "cropped_image_id": cropped_id,
                "num_colors": 12,
                "size": 3,
                "mode": "square",
            },
        )
        assert sq_res.status_code == 200
        sq_palette = sq_res.json()["palette"]

        ci_res = client.post(
            "/api/process",
            json={
                "cropped_image_id": cropped_id,
                "num_colors": 12,
                "size": 3,
                "mode": "circle",
            },
        )
        assert ci_res.status_code == 200
        ci_palette = ci_res.json()["palette"]

        # Same colors in same order
        assert len(sq_palette) == len(ci_palette)
        sq_hexes = [c["hex"] for c in sq_palette]
        ci_hexes = [c["hex"] for c in ci_palette]
        assert sq_hexes == ci_hexes
