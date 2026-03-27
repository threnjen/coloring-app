"""Image enhancement: contrast and saturation boost."""

import logging

import cv2
import numpy as np
from PIL import Image

from src.config import CONTRAST_FACTOR
from src.config import SATURATION_FACTOR

logger = logging.getLogger(__name__)


class ImageEnhancer:
    """Applies contrast and saturation enhancement to an image.

    Args:
        contrast_factor: Multiplier for contrast (>1 = more contrast).
        saturation_factor: Multiplier for saturation (>1 = more vivid).
    """

    def __init__(
        self,
        contrast_factor: float = CONTRAST_FACTOR,
        saturation_factor: float = SATURATION_FACTOR,
    ) -> None:
        self._contrast_factor = contrast_factor
        self._saturation_factor = saturation_factor

    def enhance(self, image: Image.Image) -> Image.Image:
        """Enhance contrast and saturation of an image.

        Args:
            image: PIL Image in RGB mode.

        Returns:
            Enhanced PIL Image in RGB mode.
        """
        logger.info("Enhancing image %dx%d", image.width, image.height)
        img_array = np.array(image.convert("RGB"))

        img_array = self._enhance_contrast(img_array)
        img_array = self._enhance_saturation(img_array)

        return Image.fromarray(img_array)

    def _enhance_contrast(self, img: np.ndarray) -> np.ndarray:
        """Boost contrast by scaling pixel values around the mean."""
        lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
        l_channel = lab[:, :, 0].astype(np.float32)
        mean_l = l_channel.mean()
        l_channel = np.clip(
            mean_l + self._contrast_factor * (l_channel - mean_l), 0, 255
        ).astype(np.uint8)
        lab[:, :, 0] = l_channel
        return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    def _enhance_saturation(self, img: np.ndarray) -> np.ndarray:
        """Boost saturation in HSV color space."""
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * self._saturation_factor, 0, 255)
        hsv = hsv.astype(np.uint8)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
