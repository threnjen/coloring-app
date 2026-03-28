"""Integration tests for palette edit endpoint. AC2.6, AC2.7."""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import make_jpeg_bytes


def _upload_crop_process(client: TestClient, num_colors: int = 12) -> dict:
    """Upload, crop, and process an image. Returns process response body."""
    data = make_jpeg_bytes(800, 600)
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
    cropped_id = crop_res.json()["cropped_image_id"]

    process_res = client.post(
        "/api/process",
        json={"cropped_image_id": cropped_id, "num_colors": num_colors},
    )
    assert process_res.status_code == 200
    return process_res.json()


class TestPaletteEditEndpoint:
    """Integration tests for POST /api/palette/edit."""

    def test_palette_edit_endpoint(self, client: TestClient) -> None:
        """POST /api/palette/edit returns 200 with updated palette."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]

        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 0,
                "new_color": "#FF0000",
            },
        )
        assert edit_res.status_code == 200
        edit_body = edit_res.json()
        assert "palette" in edit_body
        assert "warnings" in edit_body
        assert edit_body["palette"][0]["hex"] == "#FF0000"

    def test_palette_edit_invalid_index(self, client: TestClient) -> None:
        """POST /api/palette/edit with out-of-range index returns 400."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]

        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 99,
                "new_color": "#FF0000",
            },
        )
        assert edit_res.status_code == 400

    def test_palette_edit_invalid_hex(self, client: TestClient) -> None:
        """POST /api/palette/edit with bad hex returns 422."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]

        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 0,
                "new_color": "not-a-hex",
            },
        )
        assert edit_res.status_code == 422

    def test_palette_edit_mosaic_not_found(self, client: TestClient) -> None:
        """POST /api/palette/edit with unknown mosaic returns 404."""
        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": "b" * 32,
                "color_index": 0,
                "new_color": "#FF0000",
            },
        )
        assert edit_res.status_code == 404

    def test_palette_edit_preserves_labels(self, client: TestClient) -> None:
        """After edit, palette labels are unchanged."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]
        original_labels = [c["label"] for c in body["palette"]]

        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 0,
                "new_color": "#AABBCC",
            },
        )
        assert edit_res.status_code == 200
        new_labels = [c["label"] for c in edit_res.json()["palette"]]
        assert new_labels == original_labels

    def test_palette_edit_preview_changes(self, client: TestClient) -> None:
        """After editing a color, the preview image bytes differ."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]

        # Get original preview
        preview_before = client.get(f"/api/preview/{mosaic_id}").content

        # Edit a color to something dramatically different
        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 0,
                "new_color": "#00FF00",
            },
        )
        assert edit_res.status_code == 200

        # Get updated preview
        preview_after = client.get(f"/api/preview/{mosaic_id}").content
        assert preview_before != preview_after


class TestColorEditRoundTrip:
    """Integration test: edit color → download PDF → verify palette persists."""

    def test_color_edit_round_trip(self, client: TestClient) -> None:
        """Edit a color, verify palette persists, then download PDF successfully."""
        body = _upload_crop_process(client)
        mosaic_id = body["mosaic_id"]

        # Edit index 0 to a specific color
        new_hex = "#ABCDEF"
        edit_res = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 0,
                "new_color": new_hex,
            },
        )
        assert edit_res.status_code == 200
        assert edit_res.json()["palette"][0]["hex"] == new_hex

        # Download PDF — it should succeed with the edited palette
        pdf_res = client.get(f"/api/pdf/{mosaic_id}")
        assert pdf_res.status_code == 200
        assert pdf_res.content[:5] == b"%PDF-"

        # Edit another color and verify both edits persist
        edit_res2 = client.post(
            "/api/palette/edit",
            json={
                "mosaic_id": mosaic_id,
                "color_index": 1,
                "new_color": "#112233",
            },
        )
        assert edit_res2.status_code == 200
        palette = edit_res2.json()["palette"]
        assert palette[0]["hex"] == new_hex  # first edit persists
        assert palette[1]["hex"] == "#112233"  # second edit applied
