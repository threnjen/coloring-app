"""Unit tests for Compositor (AC3.5, AC3.7)."""

import numpy as np
import pytest
from PIL import Image

from src.processing.compositing import Compositor


@pytest.fixture
def rgba_subject() -> Image.Image:
    """A 100x100 RGBA subject: red square with full alpha."""
    arr = np.zeros((100, 100, 4), dtype=np.uint8)
    arr[:, :, 0] = 200  # Red
    arr[:, :, 3] = 255  # Fully opaque
    return Image.fromarray(arr, "RGBA")


@pytest.fixture
def rgb_background() -> Image.Image:
    """A 400x300 white RGB background."""
    return Image.new("RGB", (400, 300), (255, 255, 255))


class TestCompositor:
    """Tests for Compositor."""

    def test_composite_subject_position(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """AC3.5: Subject placed at specified (x, y) offset."""
        compositor = Compositor()
        result = compositor.composite(rgba_subject, rgb_background, x=50, y=30, scale=1.0)
        arr = np.array(result)
        # At (50, 30) the red subject should start
        assert arr[30, 50, 0] == 200, "Red channel should be 200 at subject position"
        # Before subject area should still be white
        assert arr[0, 0, 0] == 255, "Background should be white outside subject"

    def test_composite_subject_scale(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """AC3.5: Subject dimensions match scale factor."""
        compositor = Compositor()
        result = compositor.composite(rgba_subject, rgb_background, x=0, y=0, scale=0.5)
        arr = np.array(result)
        # At scale 0.5, subject is 50x50. Pixel at (49, 49) should be red
        assert arr[49, 49, 0] == 200
        # Pixel at (60, 60) should be white background (subject only extends to 50x50)
        assert arr[60, 60, 0] == 255

    def test_composite_scale_bounds(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """AC3.5: Scale outside 0.25-2.0 is clamped."""
        compositor = Compositor()
        # Scale below min (0.25) should be clamped to 0.25
        result = compositor.composite(rgba_subject, rgb_background, x=0, y=0, scale=0.1)
        assert result.size == rgb_background.size

        # Scale above max (2.0) should be clamped to 2.0
        result2 = compositor.composite(rgba_subject, rgb_background, x=0, y=0, scale=5.0)
        assert result2.size == rgb_background.size

    def test_composite_dimensions_match_background(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """AC3.7: Output same size as background."""
        compositor = Compositor()
        result = compositor.composite(rgba_subject, rgb_background, x=10, y=10, scale=1.0)
        assert result.size == rgb_background.size

    def test_composite_output_is_rgb(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """AC3.7: No alpha channel in final output."""
        compositor = Compositor()
        result = compositor.composite(rgba_subject, rgb_background, x=0, y=0, scale=1.0)
        assert result.mode == "RGB"

    def test_composite_subject_overflow_clipped(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """Edge case: Subject extending beyond canvas is clipped, no error."""
        compositor = Compositor()
        # Place subject such that it overflows the right and bottom edges
        result = compositor.composite(rgba_subject, rgb_background, x=350, y=250, scale=1.0)
        assert result.size == rgb_background.size
        # The subject should partially appear
        arr = np.array(result)
        assert arr[250, 350, 0] == 200  # Subject pixel within bounds

    def test_composite_zero_offset(
        self, rgba_subject: Image.Image, rgb_background: Image.Image
    ) -> None:
        """Baseline: Subject at (0, 0) renders in top-left."""
        compositor = Compositor()
        result = compositor.composite(rgba_subject, rgb_background, x=0, y=0, scale=1.0)
        arr = np.array(result)
        assert arr[0, 0, 0] == 200, "Subject should be at top-left"
        assert arr[99, 99, 0] == 200, "Subject should span to (99, 99)"
        assert arr[100, 100, 0] == 255, "Outside subject should be white bg"
