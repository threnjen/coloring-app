"""Core data models for mosaic coloring sheets."""

from dataclasses import dataclass
from dataclasses import field

import numpy as np

from src.config import LABEL_CHARS


@dataclass
class ColorPalette:
    """A palette of quantized colors with labels.

    Args:
        colors_rgb: Nx3 array of RGB colors (0–255).
    """

    colors_rgb: np.ndarray

    @property
    def count(self) -> int:
        """Number of colors in the palette."""
        return len(self.colors_rgb)

    def label(self, index: int) -> str:
        """Return the single-character label for a color index.

        Args:
            index: Color index (0-based).

        Returns:
            Single character: '0'-'9' then 'A'-'J'.

        Raises:
            IndexError: If index is out of range.
        """
        if index < 0 or index >= self.count:
            raise IndexError(f"Color index {index} out of range [0, {self.count})")
        return LABEL_CHARS[index]

    def hex_color(self, index: int) -> str:
        """Return the hex color string for a color index.

        Args:
            index: Color index (0-based).

        Returns:
            Hex string like '#FF00AA'.
        """
        r, g, b = self.colors_rgb[index]
        return f"#{int(r):02X}{int(g):02X}{int(b):02X}"


@dataclass
class GridCell:
    """A single cell in the mosaic grid.

    Args:
        row: Row index (0-based).
        col: Column index (0-based).
        color_index: Index into the ColorPalette.
        label: Single-character label for this cell's color.
    """

    row: int
    col: int
    color_index: int
    label: str


@dataclass
class MosaicSheet:
    """A complete mosaic sheet: grid + palette + metadata.

    Args:
        mosaic_id: Unique identifier.
        grid: 2D list of GridCell objects [row][col].
        palette: The color palette used.
        columns: Number of grid columns.
        rows: Number of grid rows.
        component_size_mm: Cell size in millimeters.
    """

    mosaic_id: str
    grid: list[list[GridCell]]
    palette: ColorPalette
    columns: int
    rows: int
    component_size_mm: float = 3.0
