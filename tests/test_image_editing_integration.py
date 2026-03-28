"""Integration tests for Phase 3 image editing endpoints."""

from unittest.mock import patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import make_png_bytes, upload_and_crop


@pytest.fixture
def client():
    from src.main import app

    return TestClient(app)


def _mock_rembg_remove(image, **kwargs):
    """Mock rembg.remove that creates a simple RGBA output."""
    arr = np.array(image)
    h, w = arr.shape[:2]
    alpha = np.zeros((h, w), dtype=np.uint8)
    # Make a rough subject mask — center 60% opaque
    margin_h, margin_w = h // 5, w // 5
    alpha[margin_h : h - margin_h, margin_w : w - margin_w] = 255
    rgba = np.dstack([arr, alpha])
    return Image.fromarray(rgba, "RGBA")


def _cutout_image(client: TestClient, cropped_id: str) -> str:
    """Helper: run cutout and return cutout_image_id."""
    with patch("src.processing.cutout.remove", side_effect=_mock_rembg_remove):
        res = client.post("/api/cutout", json={"image_id": cropped_id})
    assert res.status_code == 200
    return res.json()["cutout_image_id"]


class TestCutoutEndpoint:
    """Tests for POST /api/cutout."""

    def test_cutout_endpoint(self, client: TestClient) -> None:
        """POST valid image_id → 200 + cutout_image_id."""
        cropped_id = upload_and_crop(client)
        with patch("src.processing.cutout.remove", side_effect=_mock_rembg_remove):
            res = client.post("/api/cutout", json={"image_id": cropped_id})
        assert res.status_code == 200
        data = res.json()
        assert "cutout_image_id" in data
        assert data["width"] > 0
        assert data["height"] > 0

    def test_cutout_invalid_id(self, client: TestClient) -> None:
        """POST bad ID → 400."""
        res = client.post("/api/cutout", json={"image_id": "not-a-valid-id!!!"})
        assert res.status_code == 400

    def test_cutout_nonexistent_image(self, client: TestClient) -> None:
        """POST missing ID → 404."""
        res = client.post("/api/cutout", json={"image_id": "a" * 32})
        assert res.status_code == 404


class TestBackgroundsEndpoint:
    """Tests for GET /api/backgrounds."""

    def test_backgrounds_endpoint(self, client: TestClient) -> None:
        """GET → 200 + non-empty list with expected fields."""
        res = client.get("/api/backgrounds")
        assert res.status_code == 200
        data = res.json()
        assert "backgrounds" in data
        assert len(data["backgrounds"]) >= 9  # At least the programmatic ones
        bg = data["backgrounds"][0]
        assert "id" in bg
        assert "name" in bg
        assert "type" in bg


class TestCompositeEndpoint:
    """Tests for POST /api/composite."""

    def test_composite_with_preset_bg(self, client: TestClient) -> None:
        """POST cutout_id + background_id + position/scale → 200."""
        cropped_id = upload_and_crop(client)
        cutout_id = _cutout_image(client, cropped_id)

        res = client.post(
            "/api/composite",
            json={
                "cutout_image_id": cutout_id,
                "background_id": "solid-white",
                "x": 10,
                "y": 20,
                "scale": 1.0,
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert "composite_image_id" in data
        assert data["width"] > 0
        assert data["height"] > 0

    def test_composite_with_custom_upload(self, client: TestClient) -> None:
        """POST cutout_id + uploaded file → 200."""
        cropped_id = upload_and_crop(client)
        cutout_id = _cutout_image(client, cropped_id)

        bg_bytes = make_png_bytes(600, 400)
        res = client.post(
            "/api/composite",
            data={"cutout_image_id": cutout_id, "x": "0", "y": "0", "scale": "1.0"},
            files={"background_file": ("bg.png", bg_bytes, "image/png")},
        )
        assert res.status_code == 200
        data = res.json()
        assert "composite_image_id" in data

    def test_composite_invalid_cutout_id(self, client: TestClient) -> None:
        """POST bad cutout ID → 400."""
        res = client.post(
            "/api/composite",
            json={
                "cutout_image_id": "invalid!!!",
                "background_id": "solid-white",
            },
        )
        assert res.status_code == 400


class TestCutoutImageEndpoint:
    """Tests for GET /api/cutout/{cutout_id}/image."""

    def test_cutout_image_endpoint(self, client: TestClient) -> None:
        """GET valid cutout_id → 200 + PNG."""
        cropped_id = upload_and_crop(client)
        cutout_id = _cutout_image(client, cropped_id)

        res = client.get(f"/api/cutout/{cutout_id}/image")
        assert res.status_code == 200
        assert res.headers["content-type"] == "image/png"

    def test_cutout_image_invalid_id(self, client: TestClient) -> None:
        """GET bad cutout ID → 400."""
        res = client.get("/api/cutout/not-valid!!!/image")
        assert res.status_code == 400

    def test_cutout_image_nonexistent(self, client: TestClient) -> None:
        """GET missing cutout ID → 404."""
        res = client.get(f"/api/cutout/{'a' * 32}/image")
        assert res.status_code == 404


class TestPipelineIntegration:
    """End-to-end pipeline integration tests."""

    def test_cutout_to_pdf_pipeline(self, client: TestClient) -> None:
        """Upload → crop → cutout → composite → process → PDF → all 200."""
        cropped_id = upload_and_crop(client)
        cutout_id = _cutout_image(client, cropped_id)

        # Composite
        comp_res = client.post(
            "/api/composite",
            json={
                "cutout_image_id": cutout_id,
                "background_id": "solid-sky-blue",
                "x": 0,
                "y": 0,
                "scale": 1.0,
            },
        )
        assert comp_res.status_code == 200
        composite_id = comp_res.json()["composite_image_id"]

        # Process (using composite as input)
        proc_res = client.post(
            "/api/process",
            json={"cropped_image_id": composite_id, "num_colors": 8},
        )
        assert proc_res.status_code == 200
        mosaic_id = proc_res.json()["mosaic_id"]

        # PDF
        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"

    def test_skip_editing_pipeline(self, client: TestClient) -> None:
        """Upload → crop → process (no cutout) → PDF → all 200."""
        cropped_id = upload_and_crop(client)

        proc_res = client.post(
            "/api/process",
            json={"cropped_image_id": cropped_id, "num_colors": 8},
        )
        assert proc_res.status_code == 200
        mosaic_id = proc_res.json()["mosaic_id"]

        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
