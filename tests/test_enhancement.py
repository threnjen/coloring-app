"""Tests for image enhancement. Maps to AC2.5."""

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
        enhancer = ImageEnhancer()
        original_std = np.array(low_contrast_image).astype(float).std()

        enhanced = enhancer.enhance(low_contrast_image)
        enhanced_std = np.array(enhanced).astype(float).std()

        assert enhanced_std > original_std

    def test_enhancement_increases_saturation(
        self, sample_rgb_image: Image.Image
    ) -> None:
        """Given a colored image, when enhanced, then mean saturation in HSV increases."""
        enhancer = ImageEnhancer()

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

    # --- CLAHE contrast ---

    def test_clahe_improves_local_contrast(
        self, low_contrast_image: Image.Image
    ) -> None:
        """CLAHE must increase mean local L-channel variance across 4x4 tiles."""
        enhancer = ImageEnhancer()
        arr = np.array(low_contrast_image)
        lab_before = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
        l_before = lab_before[:, :, 0].astype(float)

        h, w = l_before.shape
        th, tw = h // 4, w // 4

        def mean_tile_var(l_ch: np.ndarray) -> float:
            return float(
                np.mean(
                    [
                        l_ch[i * th : (i + 1) * th, j * tw : (j + 1) * tw].var()
                        for i in range(4)
                        for j in range(4)
                    ]
                )
            )

        var_before = mean_tile_var(l_before)

        enhanced = enhancer.enhance(low_contrast_image)
        lab_after = cv2.cvtColor(np.array(enhanced), cv2.COLOR_RGB2LAB)
        l_after = lab_after[:, :, 0].astype(float)
        var_after = mean_tile_var(l_after)

        assert var_after > var_before * 1.2

    def test_clahe_preserves_dimensions(self, sample_rgb_image: Image.Image) -> None:
        """CLAHE contrast enhancement must not change image dimensions."""
        enhancer = ImageEnhancer()
        enhanced = enhancer.enhance(sample_rgb_image)
        assert enhanced.size == sample_rgb_image.size

    # --- Saturation curve ---

    def test_saturation_curve_boosts_midrange(self) -> None:
        """Saturation curve gives more relative boost to lower-S than higher-S pixels."""
        enhancer = ImageEnhancer()
        # Low-S: HSV ~(0, 51, 200) == RGB(200, 160, 160)
        # High-S: HSV ~(0, 160, 200) == RGB(200, 74, 74)
        # With linear multiplication both get the same relative boost;
        # the curve gives diminishing returns as S approaches 255.
        arr = np.array([[[200, 160, 160], [200, 74, 74]]], dtype=np.uint8)

        hsv_before = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
        s_low_before = int(hsv_before[0, 0, 1])
        s_high_before = int(hsv_before[0, 1, 1])

        result = enhancer._enhance_saturation(arr)

        hsv_after = cv2.cvtColor(result, cv2.COLOR_RGB2HSV)
        s_low_after = int(hsv_after[0, 0, 1])
        s_high_after = int(hsv_after[0, 1, 1])

        rel_boost_low = (s_low_after - s_low_before) / s_low_before
        rel_boost_high = (s_high_after - s_high_before) / s_high_before

        assert rel_boost_low > rel_boost_high

    def test_saturation_preserves_range(self, sample_rgb_image: Image.Image) -> None:
        """No pixel S-channel value must exceed 255 after saturation enhancement."""
        enhancer = ImageEnhancer()
        arr = np.array(sample_rgb_image)
        result = enhancer._enhance_saturation(arr)
        hsv = cv2.cvtColor(result, cv2.COLOR_RGB2HSV)
        assert int(hsv[:, :, 1].max()) <= 255
        assert int(hsv[:, :, 1].min()) >= 0

    # --- Edge-aware sharpening ---

    def test_edge_sharpening_increases_detail(
        self, sample_rgb_image: Image.Image
    ) -> None:
        """_sharpen must increase Laplacian variance (edge detail) of the image."""
        enhancer = ImageEnhancer()
        arr = np.array(sample_rgb_image)

        def laplacian_variance(img_arr: np.ndarray) -> float:
            gray = cv2.cvtColor(img_arr, cv2.COLOR_RGB2GRAY)
            return cv2.Laplacian(gray, cv2.CV_64F).var()

        var_before = laplacian_variance(arr)
        sharpened = enhancer._sharpen(arr)
        var_after = laplacian_variance(sharpened)

        assert var_after > var_before

    def test_edge_sharpening_no_noise_amplification(self) -> None:
        """_sharpen must not significantly increase std dev in flat image regions."""
        enhancer = ImageEnhancer()
        rng = np.random.default_rng(42)
        base = np.full((100, 100, 3), 128, dtype=np.int32)
        noise = rng.integers(-3, 4, size=(100, 100, 3))
        flat_arr = np.clip(base + noise, 0, 255).astype(np.uint8)

        std_before = flat_arr.astype(float).std()
        sharpened = enhancer._sharpen(flat_arr)
        std_after = sharpened.astype(float).std()

        assert std_after < std_before * 2
