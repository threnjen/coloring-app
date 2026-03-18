"""Preview image generation from mosaic grid data."""

import logging

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from src.models.mosaic import ColorPalette
from src.models.mosaic import GridCell

logger = logging.getLogger(__name__)

PREVIEW_CELL_PX: int = 12


class PreviewRenderer:
    """Renders a colored grid preview image from mosaic data.

    Args:
        cell_size: Size of each cell in pixels for the preview image.
    """

    def __init__(self, cell_size: int = PREVIEW_CELL_PX) -> None:
        self._cell_size = cell_size

    def render(self, grid: list[list[GridCell]], palette: ColorPalette) -> Image.Image:
        """Generate a preview PNG image of the mosaic grid.

        Args:
            grid: 2D list of GridCell objects.
            palette: Color palette for rendering.

        Returns:
            PIL Image with colored cells and labels.
        """
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        width = cols * self._cell_size
        height = rows * self._cell_size

        logger.info("Rendering preview %dx%d px (%dx%d cells)", width, height, cols, rows)

        img = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(img)

        font_size = max(7, self._cell_size - 4)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (OSError, IOError):
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except (OSError, IOError):
                logger.warning("No TrueType font found; falling back to default bitmap font")
                font = ImageFont.load_default()

        for row_cells in grid:
            for cell in row_cells:
                x0 = cell.col * self._cell_size
                y0 = cell.row * self._cell_size
                x1 = x0 + self._cell_size - 1
                y1 = y0 + self._cell_size - 1

                rgb = tuple(int(v) for v in palette.colors_rgb[cell.color_index])
                draw.rectangle([x0, y0, x1, y1], fill=rgb)

                # Choose label color: white on dark, black on light
                brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                label_color = "white" if brightness < 128 else "black"

                bbox = draw.textbbox((0, 0), cell.label, font=font)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                tx = x0 + (self._cell_size - tw) / 2
                ty = y0 + (self._cell_size - th) / 2
                draw.text((tx, ty), cell.label, fill=label_color, font=font)

        return img
