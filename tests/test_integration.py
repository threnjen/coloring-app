"""Integration tests for the full pipeline. Maps to AC1.1–AC1.10."""

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
    arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width: int = 400, height: int = 300, mode: str = "RGB") -> bytes:
    """Create a PNG image in memory."""
    if mode == "RGBA":
        arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 4), dtype=np.uint8)
    else:
        arr = np.random.default_rng(42).integers(0, 255, size=(height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestUpload:
    """Tests for the upload endpoint."""

    def test_upload_valid_jpeg(self, client: TestClient) -> None:
        """Upload a valid JPEG succeeds."""
        data = _make_jpeg_bytes()
        res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
        assert res.status_code == 200
        body = res.json()
        assert "image_id" in body
        assert body["width"] == 400
        assert body["height"] == 300

    def test_upload_valid_png(self, client: TestClient) -> None:
        """Upload a valid PNG succeeds."""
        data = _make_png_bytes()
        res = client.post("/api/upload", files={"file": ("test.png", data, "image/png")})
        assert res.status_code == 200
        assert "image_id" in res.json()

    def test_upload_invalid_file(self, client: TestClient) -> None:
        """Upload a text file returns 400."""
        res = client.post(
            "/api/upload",
            files={"file": ("test.txt", b"not an image", "text/plain")},
        )
        assert res.status_code == 400

    def test_upload_oversized(self, client: TestClient) -> None:
        """Upload an oversized file returns 400."""
        # Create data larger than 20MB
        data = b"\xff\xd8\xff" + b"\x00" * (21 * 1024 * 1024)
        res = client.post(
            "/api/upload",
            files={"file": ("big.jpg", data, "image/jpeg")},
        )
        assert res.status_code == 400


class TestCrop:
    """Tests for the crop endpoint."""

    def test_crop_valid_region(self, client: TestClient) -> None:
        """Crop a valid region succeeds."""
        data = _make_jpeg_bytes(400, 300)
        upload_res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
        image_id = upload_res.json()["image_id"]

        crop_res = client.post(
            "/api/crop",
            json={"image_id": image_id, "x": 50, "y": 50, "width": 200, "height": 150},
        )
        assert crop_res.status_code == 200
        body = crop_res.json()
        assert body["width"] == 200
        assert body["height"] == 150

    def test_crop_too_small(self, client: TestClient) -> None:
        """Crop region < 50px returns 400."""
        data = _make_jpeg_bytes(400, 300)
        upload_res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
        image_id = upload_res.json()["image_id"]

        crop_res = client.post(
            "/api/crop",
            json={"image_id": image_id, "x": 0, "y": 0, "width": 10, "height": 10},
        )
        assert crop_res.status_code == 400

    def test_crop_out_of_bounds(self, client: TestClient) -> None:
        """Crop region exceeding image bounds returns 400."""
        data = _make_jpeg_bytes(400, 300)
        upload_res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
        image_id = upload_res.json()["image_id"]

        crop_res = client.post(
            "/api/crop",
            json={"image_id": image_id, "x": 300, "y": 200, "width": 200, "height": 200},
        )
        assert crop_res.status_code == 400


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline(self, client: TestClient) -> None:
        """Upload → crop → process → preview → PDF all succeed."""
        # Upload
        data = _make_jpeg_bytes(800, 600)
        upload_res = client.post("/api/upload", files={"file": ("test.jpg", data, "image/jpeg")})
        assert upload_res.status_code == 200
        image_id = upload_res.json()["image_id"]

        # Crop
        crop_res = client.post(
            "/api/crop",
            json={"image_id": image_id, "x": 50, "y": 50, "width": 600, "height": 400},
        )
        assert crop_res.status_code == 200
        cropped_id = crop_res.json()["cropped_image_id"]

        # Process
        process_res = client.post(
            "/api/process",
            json={"cropped_image_id": cropped_id, "num_colors": 12},
        )
        assert process_res.status_code == 200
        body = process_res.json()
        assert body["num_colors"] == 12
        assert body["columns"] == 50
        assert body["rows"] == 65
        assert len(body["palette"]) == 12
        mosaic_id = body["mosaic_id"]

        # Preview
        preview_res = client.get(f"/api/preview/{mosaic_id}")
        assert preview_res.status_code == 200
        assert preview_res.headers["content-type"] == "image/png"

        # PDF
        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
        assert pdf_res.headers["content-type"] == "application/pdf"
        assert pdf_res.content[:5] == b"%PDF-"

    def test_transparent_png_handling(self, client: TestClient) -> None:
        """Transparent PNG is converted to RGB and processes successfully."""
        data = _make_png_bytes(400, 300, mode="RGBA")
        upload_res = client.post("/api/upload", files={"file": ("test.png", data, "image/png")})
        assert upload_res.status_code == 200

    def test_process_not_found(self, client: TestClient) -> None:
        """Processing a non-existent image returns 404."""
        res = client.post(
            "/api/process",
            json={"cropped_image_id": "a" * 32, "num_colors": 12},
        )
        assert res.status_code == 404

    def test_preview_not_found(self, client: TestClient) -> None:
        """Preview for non-existent mosaic returns 404."""
        res = client.get("/api/preview/" + "a" * 32)
        assert res.status_code == 404

    def test_pdf_not_found(self, client: TestClient) -> None:
        """PDF for non-existent mosaic returns 404."""
        res = client.get("/api/pdf/" + "a" * 32)
        assert res.status_code == 404
