"""Unit tests for CutoutProcessor (AC3.1, AC3.2)."""

import numpy as np
import pytest
from PIL import Image

from src.processing.cutout import CutoutProcessor


@pytest.fixture
def subject_on_background() -> Image.Image:
    """A 200x200 image with a bright red square subject on a white background."""
    arr = np.full((200, 200, 3), 255, dtype=np.uint8)  # white background
    arr[50:150, 50:150] = [200, 30, 30]  # red subject in center
    return Image.fromarray(arr, "RGB")


class TestCutoutProcessor:
    """Tests for CutoutProcessor."""

    def test_cutout_produces_rgba(self, subject_on_background: Image.Image) -> None:
        """AC3.1: Output has 4 channels (RGBA) and alpha is non-trivial."""
        processor = CutoutProcessor()
        rgba, _mask = processor.remove_background(subject_on_background)

        assert rgba.mode == "RGBA"
        alpha = np.array(rgba)[:, :, 3]
        # Alpha should have both transparent and opaque regions
        assert alpha.min() < 128, "Expected some transparent pixels"
        assert alpha.max() > 128, "Expected some opaque pixels"

    def test_cutout_returns_mask(self, subject_on_background: Image.Image) -> None:
        """AC3.1: Separate grayscale mask returned, same dimensions as input."""
        processor = CutoutProcessor()
        rgba, mask = processor.remove_background(subject_on_background)

        assert mask.mode == "L"
        assert mask.size == subject_on_background.size
        assert mask.size == rgba.size

    def test_cutout_mask_is_smooth(self, subject_on_background: Image.Image) -> None:
        """AC3.2: Mask edges are not jagged — edge gradient variance is low."""
        processor = CutoutProcessor()
        _rgba, mask = processor.remove_background(subject_on_background)

        mask_arr = np.array(mask, dtype=np.float64)
        # Compute gradients at edges
        grad_x = np.abs(np.diff(mask_arr, axis=1))
        grad_y = np.abs(np.diff(mask_arr, axis=0))

        # Get only edge pixels (where gradient is non-zero)
        edge_grads_x = grad_x[grad_x > 0]
        edge_grads_y = grad_y[grad_y > 0]

        if len(edge_grads_x) > 0:
            # Smooth edges should have gradual transitions, not all max jumps
            # A jagged binary mask would have all edges at 255 (max jump)
            assert edge_grads_x.mean() < 200, "Mask edges appear jagged (x-axis)"
        if len(edge_grads_y) > 0:
            assert edge_grads_y.mean() < 200, "Mask edges appear jagged (y-axis)"

    def test_cutout_mask_feathered(self, subject_on_background: Image.Image) -> None:
        """AC3.2: Alpha values between 0-255 exist at edges (feathering)."""
        processor = CutoutProcessor()
        rgba, _mask = processor.remove_background(subject_on_background)

        alpha = np.array(rgba)[:, :, 3]
        # Feathered edges should have intermediate alpha values
        intermediate = (alpha > 10) & (alpha < 245)
        assert intermediate.sum() > 0, "No intermediate alpha values — edges not feathered"
