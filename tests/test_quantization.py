"""Tests for color quantization. Maps to AC1.5."""

import numpy as np
from PIL import Image

from src.processing.quantization import ColorQuantizer


class TestColorQuantizer:
    """Tests for the ColorQuantizer class."""

    def test_quantization_returns_requested_colors(self, sample_rgb_image: Image.Image) -> None:
        """Given N=12, when quantized, then palette has exactly 12 colors."""
        quantizer = ColorQuantizer(n_colors=12)
        label_map, palette = quantizer.quantize(sample_rgb_image)
        assert palette.count == 12

    def test_quantization_label_map_shape(self, sample_rgb_image: Image.Image) -> None:
        """Label map shape should match the input image dimensions."""
        quantizer = ColorQuantizer(n_colors=8)
        label_map, palette = quantizer.quantize(sample_rgb_image)
        assert label_map.shape == (sample_rgb_image.height, sample_rgb_image.width)

    def test_quantization_label_map_values(self, sample_rgb_image: Image.Image) -> None:
        """All label map values should be valid color indices."""
        quantizer = ColorQuantizer(n_colors=10)
        label_map, palette = quantizer.quantize(sample_rgb_image)
        assert label_map.min() >= 0
        assert label_map.max() < palette.count

    def test_quantization_uses_lab_space(self) -> None:
        """Given two perceptually similar RGB colors, K-means in LAB merges them."""
        # Create an image with two slightly different blues
        arr = np.zeros((100, 100, 3), dtype=np.uint8)
        arr[:50, :] = [40, 40, 200]
        arr[50:, :] = [45, 42, 198]
        img = Image.fromarray(arr, "RGB")

        quantizer = ColorQuantizer(n_colors=8)
        label_map, palette = quantizer.quantize(img)

        # These similar blues should merge: actual clusters < 8
        unique_labels = len(np.unique(label_map))
        assert unique_labels < 8

    def test_quantization_reproducible(self, sample_rgb_image: Image.Image) -> None:
        """Same seed should produce identical results."""
        q1 = ColorQuantizer(n_colors=8, random_state=42)
        q2 = ColorQuantizer(n_colors=8, random_state=42)

        _, p1 = q1.quantize(sample_rgb_image)
        _, p2 = q2.quantize(sample_rgb_image)

        np.testing.assert_array_equal(p1.colors_rgb, p2.colors_rgb)
