"""Tests for image enhancement. Maps to AC1.3."""

import cv2
import numpy as np
from PIL import Image

from src.processing.enhancement import ImageEnhancer


class TestImageEnhancer:
    """Tests for the ImageEnhancer class."""

    def test_enhancement_increases_contrast(
        self, low_contrast_image: Image.Image
    ) -> None:
        """Given a low-contrast image, when enhanced, then pixel std dev increases."""
        enhancer = ImageEnhancer(contrast_factor=1.5, saturation_factor=1.0)
        original_std = np.array(low_contrast_image).astype(float).std()

        enhanced = enhancer.enhance(low_contrast_image)
        enhanced_std = np.array(enhanced).astype(float).std()

        assert enhanced_std > original_std

    def test_enhancement_increases_saturation(
        self, sample_rgb_image: Image.Image
    ) -> None:
        """Given a colored image, when enhanced, then mean saturation in HSV increases."""
        enhancer = ImageEnhancer(contrast_factor=1.0, saturation_factor=1.5)

        original_hsv = cv2.cvtColor(np.array(sample_rgb_image), cv2.COLOR_RGB2HSV)
        original_sat = original_hsv[:, :, 1].mean()

        enhanced = enhancer.enhance(sample_rgb_image)
        enhanced_hsv = cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2HSV)
        enhanced_sat = enhanced_hsv[:, :, 1].mean()

        assert enhanced_sat > original_sat

    def test_enhancement_preserves_dimensions(
        self, sample_rgb_image: Image.Image
    ) -> None:
        """Enhancement should not change image dimensions."""
        enhancer = ImageEnhancer()
        enhanced = enhancer.enhance(sample_rgb_image)
        assert enhanced.size == sample_rgb_image.size

    def test_enhancement_returns_rgb(self, sample_rgb_image: Image.Image) -> None:
        """Enhancement should return an RGB image."""
        enhancer = ImageEnhancer()
        enhanced = enhancer.enhance(sample_rgb_image)
        assert enhanced.mode == "RGB"
