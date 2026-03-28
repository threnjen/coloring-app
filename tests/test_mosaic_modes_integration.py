"""Integration tests for mosaic mode pipeline. AC2.1, AC2.8."""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from tests.conftest import make_jpeg_bytes, upload_and_crop


class TestPipelineCircleMode:
    """Integration tests for circle mode pipeline."""

    def test_pipeline_circle_mode(self, client: TestClient) -> None:
        """Full pipeline with mode=circle produces valid PDF."""
        cropped_id = upload_and_crop(client)

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
        cropped_id = upload_and_crop(client)

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
        cropped_id = upload_and_crop(client)

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
