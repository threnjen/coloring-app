"""Alpha compositing: place a cutout subject onto a background."""

import logging
import time

from PIL import Image

from src.config import COMPOSITE_MAX_SCALE, COMPOSITE_MIN_SCALE

logger = logging.getLogger(__name__)


class Compositor:
    """Composites an RGBA subject onto an RGB background at a given position/scale.

    Stateless — scale bounds come from config constants.
    """

    def composite(
        self,
        subject: Image.Image,
        background: Image.Image,
        x: int,
        y: int,
        scale: float,
    ) -> Image.Image:
        """Place subject onto background at (x, y) with given scale.

        Args:
            subject: RGBA image (cutout with alpha mask).
            background: RGB image to composite onto.
            x: Horizontal offset in pixels.
            y: Vertical offset in pixels.
            scale: Scale factor for subject (clamped to config bounds).

        Returns:
            RGB image with same dimensions as background.
        """
        t0 = time.monotonic()
        scale = max(COMPOSITE_MIN_SCALE, min(COMPOSITE_MAX_SCALE, scale))
        logger.info(
            "Compositing subject onto %dx%d background at (%d, %d) scale=%.2f",
            background.width,
            background.height,
            x,
            y,
            scale,
        )

        # Scale subject
        new_w = max(1, int(subject.width * scale))
        new_h = max(1, int(subject.height * scale))
        scaled = subject.resize((new_w, new_h), Image.LANCZOS)

        # Work on a copy of the background
        result = background.copy().convert("RGBA")

        # Paste with alpha mask — PIL handles clipping for out-of-bounds
        result.paste(scaled, (x, y), scaled.split()[3])

        # Convert back to RGB
        rgb_result = result.convert("RGB")

        elapsed = time.monotonic() - t0
        logger.info("Compositing complete: %.2fs", elapsed)

        return rgb_result
