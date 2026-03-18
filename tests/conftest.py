"""Shared test fixtures."""

import numpy as np
import pytest
from PIL import Image


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
