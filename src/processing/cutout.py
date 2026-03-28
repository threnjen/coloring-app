"""Background removal using rembg with mask cleanup."""

import logging
import time

import cv2
import numpy as np
from PIL import Image
from rembg import remove

from src.config import CUTOUT_MASK_BLUR_RADIUS, CUTOUT_MORPH_KERNEL_SIZE

logger = logging.getLogger(__name__)


class CutoutProcessor:
    """Removes image backgrounds via rembg and cleans the resulting alpha mask.

    Stateless — all parameters come from config constants.
    """

    def remove_background(self, image: Image.Image) -> tuple[Image.Image, Image.Image]:
        """Remove background from an RGB image.

        Args:
            image: PIL Image in RGB mode.

        Returns:
            Tuple of (RGBA subject image with cleaned alpha, grayscale mask).
        """
        t0 = time.monotonic()
        logger.info("Removing background from %dx%d image", image.width, image.height)

        # rembg returns RGBA with alpha mask
        rgba = remove(image)
        if rgba.mode != "RGBA":
            rgba = rgba.convert("RGBA")

        # Extract and clean the alpha channel
        alpha = np.array(rgba.split()[3])
        cleaned_alpha = self._clean_mask(alpha)

        # Replace alpha with cleaned version
        r, g, b, _ = rgba.split()
        cleaned_mask_img = Image.fromarray(cleaned_alpha, "L")
        rgba = Image.merge("RGBA", (r, g, b, cleaned_mask_img))

        elapsed = time.monotonic() - t0
        logger.info("Background removal complete: %.2fs", elapsed)

        return rgba, cleaned_mask_img

    @staticmethod
    def _clean_mask(mask: np.ndarray) -> np.ndarray:
        """Clean a binary/grayscale mask with morphology and feathering.

        Args:
            mask: 2D uint8 array (alpha channel).

        Returns:
            Cleaned and feathered uint8 mask.
        """
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE,
            (CUTOUT_MORPH_KERNEL_SIZE, CUTOUT_MORPH_KERNEL_SIZE),
        )

        # Morphological close (fill small holes)
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        # Morphological open (remove small noise)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)

        # Gaussian blur for feathered edges
        if CUTOUT_MASK_BLUR_RADIUS > 0:
            ksize = CUTOUT_MASK_BLUR_RADIUS * 2 + 1
            cleaned = cv2.GaussianBlur(cleaned, (ksize, ksize), 0)

        return cleaned
