"""Preview image generation from mosaic grid data."""

import logging
import math

from PIL import Image, ImageDraw, ImageFont

from src.models.mosaic import ColorPalette, GridCell
from src.rendering.color_utils import perceived_brightness
from src.rendering.geometry import hex_vertices

logger = logging.getLogger(__name__)

PREVIEW_CELL_PX: int = 12


class PreviewRenderer:
    """Renders a colored grid preview image from mosaic data.

    Args:
        cell_size: Size of each cell in pixels for the preview image.
    """

    def __init__(self, cell_size: int = PREVIEW_CELL_PX) -> None:
        self._cell_size = cell_size

    def render(
        self, grid: list[list[GridCell]], palette: ColorPalette, mode: str = "square"
    ) -> Image.Image:
        """Generate a preview PNG image of the mosaic grid.

        Args:
            grid: 2D list of GridCell objects.
            palette: Color palette for rendering.
            mode: Rendering mode ('square', 'circle', or 'hexagon').

        Returns:
            PIL Image with colored cells and labels.
        """
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0

        if mode == "hexagon":
            col_spacing = self._cell_size
            row_spacing = int(self._cell_size * math.sqrt(3) / 2)
            # Account for odd-row offset overshoot
            width = cols * col_spacing + col_spacing // 2
            height = rows * row_spacing + row_spacing
        else:
            width = cols * self._cell_size
            height = rows * self._cell_size

        logger.info(
            "Rendering preview %dx%d px (%dx%d cells, mode=%s)",
            width,
            height,
            cols,
            rows,
            mode,
        )

        bg_color = "black" if mode != "square" else "white"
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        font_size = max(7, self._cell_size - 4)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size
            )
        except (OSError, IOError):
            try:
                font = ImageFont.truetype(
                    "/System/Library/Fonts/Helvetica.ttc", font_size
                )
            except (OSError, IOError):
                logger.warning(
                    "No TrueType font found; falling back to default bitmap font"
                )
                font = ImageFont.load_default()

        for row_cells in grid:
            for cell in row_cells:
                if mode == "square":
                    self._draw_square_cell(draw, cell, palette, font)
                elif mode == "circle":
                    self._draw_circle_cell(draw, cell, palette, font)
                elif mode == "hexagon":
                    self._draw_hexagon_cell(draw, cell, palette, font)
                else:
                    raise ValueError(f"Unsupported mode: {mode!r}")

        return img

    @staticmethod
    def _label_color_for_rgb(rgb: tuple[int, int, int]) -> str:
        """Return 'white' or 'black' for optimal contrast against the given RGB color."""
        brightness = perceived_brightness(rgb[0], rgb[1], rgb[2])
        return "white" if brightness < 128 else "black"

    def _draw_square_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell: GridCell,
        palette: ColorPalette,
        font: ImageFont.FreeTypeFont,
    ) -> None:
        """Draw a single square cell with color fill and label."""
        x0 = cell.col * self._cell_size
        y0 = cell.row * self._cell_size
        x1 = x0 + self._cell_size - 1
        y1 = y0 + self._cell_size - 1

        rgb = tuple(int(v) for v in palette.colors_rgb[cell.color_index])
        draw.rectangle([x0, y0, x1, y1], fill=rgb)

        label_color = self._label_color_for_rgb(rgb)

        bbox = draw.textbbox((0, 0), cell.label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = x0 + (self._cell_size - tw) / 2
        ty = y0 + (self._cell_size - th) / 2
        draw.text((tx, ty), cell.label, fill=label_color, font=font)

    def _draw_circle_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell: GridCell,
        palette: ColorPalette,
        font: ImageFont.FreeTypeFont,
    ) -> None:
        """Draw a single circle cell with color fill and label."""
        gap = 1
        x0 = cell.col * self._cell_size + gap
        y0 = cell.row * self._cell_size + gap
        x1 = (cell.col + 1) * self._cell_size - 1 - gap
        y1 = (cell.row + 1) * self._cell_size - 1 - gap

        rgb = tuple(int(v) for v in palette.colors_rgb[cell.color_index])
        draw.ellipse([x0, y0, x1, y1], fill=rgb)

        label_color = self._label_color_for_rgb(rgb)

        cx = cell.col * self._cell_size + self._cell_size / 2
        cy = cell.row * self._cell_size + self._cell_size / 2
        bbox = draw.textbbox((0, 0), cell.label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = cx - tw / 2
        ty = cy - th / 2
        draw.text((tx, ty), cell.label, fill=label_color, font=font)

    def _draw_hexagon_cell(
        self,
        draw: ImageDraw.ImageDraw,
        cell: GridCell,
        palette: ColorPalette,
        font: ImageFont.FreeTypeFont,
    ) -> None:
        """Draw a single hexagon cell with color fill and label."""
        col_spacing = self._cell_size
        row_spacing = int(self._cell_size * math.sqrt(3) / 2)
        gap = 1

        cx = cell.col * col_spacing + col_spacing // 2
        cy = cell.row * row_spacing + row_spacing // 2
        if cell.row % 2 == 1:
            cx += col_spacing // 2

        # flat-to-flat = cell_size - gap*2; circumradius = flat_to_flat / sqrt(3)
        flat_to_flat = self._cell_size - gap * 2
        circumradius = flat_to_flat / math.sqrt(3)

        vertices = hex_vertices(cx, cy, circumradius)

        rgb = tuple(int(v) for v in palette.colors_rgb[cell.color_index])
        draw.polygon(vertices, fill=rgb)

        label_color = self._label_color_for_rgb(rgb)

        bbox = draw.textbbox((0, 0), cell.label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = cx - tw / 2
        ty = cy - th / 2
        draw.text((tx, ty), cell.label, fill=label_color, font=font)
