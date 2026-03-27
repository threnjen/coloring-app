"""Image enhancement: adaptive contrast, saturation curve, edge-aware sharpening."""

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """Applies adaptive contrast (CLAHE), saturation curve, and edge sharpening.

    All parameters are class-level constants; no constructor arguments are needed.
    """

    _CLAHE_CLIP_LIMIT: float = 2.0
    _CLAHE_TILE_GRID: tuple[int, int] = (8, 8)
    _SATURATION_BOOST: float = 0.4
    _SHARPEN_ALPHA: float = 0.5
    _BILATERAL_D: int = 9
    _BILATERAL_SIGMA_COLOR: float = 75
    _BILATERAL_SIGMA_SPACE: float = 75

    def enhance(self, image: Image.Image) -> Image.Image:
        """Enhance contrast, saturation, and sharpness of an image.

        Args:
            image: PIL Image in RGB mode.

        Returns:
            Enhanced PIL Image in RGB mode.
        """
        logger.info("Enhancing image %dx%d", image.width, image.height)
        img_array = np.array(image.convert("RGB"))

        img_array = self._enhance_contrast(img_array)
        img_array = self._enhance_saturation(img_array)
        img_array = self._sharpen(img_array)

        return Image.fromarray(img_array)

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Boost local contrast using CLAHE on the L channel of LAB."""
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        clahe = cv2.createCLAHE(
            clipLimit=self._CLAHE_CLIP_LIMIT,
            tileGridSize=self._CLAHE_TILE_GRID,
        )
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    def _enhance_saturation(self, img: np.ndarray) -> np.ndarray:
        """Boost saturation using a curve that gives diminishing returns at high S."""
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        s = hsv[:, :, 1]
        hsv[:, :, 1] = np.clip(
            s + self._SATURATION_BOOST * s * (1.0 - s / 255.0), 0, 255
        )
        return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

    def _sharpen(self, img: np.ndarray) -> np.ndarray:
        """Edge-aware sharpening via bilateral filter + unsharp mask."""
        bilateral = cv2.bilateralFilter(
            img,
            d=self._BILATERAL_D,
            sigmaColor=self._BILATERAL_SIGMA_COLOR,
            sigmaSpace=self._BILATERAL_SIGMA_SPACE,
        )
        img_f = img.astype(np.float32)
        sharpened = img_f + self._SHARPEN_ALPHA * (img_f - bilateral.astype(np.float32))
        return np.clip(sharpened, 0, 255).astype(np.uint8)
