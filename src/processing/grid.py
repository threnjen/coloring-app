"""Grid generation: convert a label map into a 2D array of GridCells."""

import logging

import numpy as np
from scipy import stats

from src.config import GRID_COLUMNS
from src.config import GRID_ROWS
from src.models.mosaic import ColorPalette
from src.models.mosaic import GridCell

logger = logging.getLogger(__name__)


class GridGenerator:
    """Generates a mosaic grid from a quantized label map.

    Args:
        columns: Number of grid columns.
        rows: Number of grid rows.
    """

    def __init__(self, columns: int = GRID_COLUMNS, rows: int = GRID_ROWS) -> None:
        self._columns = columns
        self._rows = rows

    def generate(
        self, label_map: np.ndarray, palette: ColorPalette
    ) -> list[list[GridCell]]:
        """Generate a 2D grid of cells by downsampling the label map.

        Each cell is assigned the most common color index in its corresponding
        region of the label map.

        Args:
            label_map: 2D array of color indices (H x W).
            palette: Color palette for label lookup.

        Returns:
            2D list of GridCell objects [row][col].
        """
        h, w = label_map.shape
        logger.info(
            "Generating %dx%d grid from %dx%d label map",
            self._columns,
            self._rows,
            w,
            h,
        )

        cell_h = h / self._rows
        cell_w = w / self._columns

        grid: list[list[GridCell]] = []
        for r in range(self._rows):
            row_cells: list[GridCell] = []
            y_start = int(r * cell_h)
            y_end = int((r + 1) * cell_h)
            for c in range(self._columns):
                x_start = int(c * cell_w)
                x_end = int((c + 1) * cell_w)
                region = label_map[y_start:y_end, x_start:x_end]
                color_index = int(stats.mode(region, axis=None, keepdims=False).mode)
                cell = GridCell(
                    row=r,
                    col=c,
                    color_index=color_index,
                    label=palette.label(color_index),
                )
                row_cells.append(cell)
            grid.append(row_cells)

        logger.info("Grid generated: %d rows × %d cols", self._rows, self._columns)
        return grid
