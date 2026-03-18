"""K-means color quantization in CIELAB color space."""

import logging

import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from src.models.mosaic import ColorPalette

logger = logging.getLogger(__name__)


class ColorQuantizer:
    """Quantizes an image to a fixed number of colors using K-means in LAB space.

    Args:
        n_colors: Number of target colors (8–20).
        random_state: Seed for reproducible K-means.
    """

    def __init__(self, n_colors: int, random_state: int = 42) -> None:
        self._n_colors = n_colors
        self._random_state = random_state

    def quantize(self, image: Image.Image) -> tuple[np.ndarray, ColorPalette]:
        """Quantize image colors via K-means in CIELAB space.

        Args:
            image: PIL Image in RGB mode.

        Returns:
            Tuple of (label_map, palette) where label_map is a 2D array of
            color indices matching image dimensions, and palette is a ColorPalette.
        """
        logger.info("Quantizing %dx%d to %d colors", image.width, image.height, self._n_colors)
        rgb = np.array(image.convert("RGB"))
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

        h, w = lab.shape[:2]
        pixels = lab.reshape(-1, 3).astype(np.float32)

        kmeans = KMeans(
            n_clusters=self._n_colors,
            random_state=self._random_state,
            n_init=10,
        )
        labels = kmeans.fit_predict(pixels)
        centers_lab = kmeans.cluster_centers_

        # Convert cluster centers back to RGB
        centers_lab_img = centers_lab.reshape(1, -1, 3).astype(np.uint8)
        centers_rgb_img = cv2.cvtColor(centers_lab_img, cv2.COLOR_LAB2RGB)
        centers_rgb = centers_rgb_img.reshape(-1, 3)

        label_map = labels.reshape(h, w)
        palette = ColorPalette(colors_rgb=centers_rgb)

        actual_count = len(np.unique(labels))
        if actual_count < self._n_colors:
            logger.warning(
                "Requested %d colors but only %d distinct clusters found",
                self._n_colors,
                actual_count,
            )

        logger.info("Quantization complete: %d colors", palette.count)
        return label_map, palette
