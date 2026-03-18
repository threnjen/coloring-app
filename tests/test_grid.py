"""Tests for grid generation. Maps to AC1.6, AC1.7."""

import numpy as np

from src.config import LABEL_CHARS
from src.models.mosaic import ColorPalette
from src.processing.grid import GridGenerator


class TestGridGenerator:
    """Tests for the GridGenerator class."""

    def test_grid_dimensions_4mm(self) -> None:
        """Given a label map, grid is 50 columns × 65 rows at 4mm."""
        label_map = np.random.default_rng(42).integers(0, 8, size=(650, 500))
        palette = ColorPalette(
            colors_rgb=np.random.default_rng(42).integers(0, 255, size=(8, 3), dtype=np.uint8)
        )
        generator = GridGenerator(columns=50, rows=65)
        grid = generator.generate(label_map, palette)

        assert len(grid) == 65
        assert len(grid[0]) == 50

    def test_grid_all_cells_have_labels(self) -> None:
        """Every cell must have a valid single-character label."""
        label_map = np.random.default_rng(42).integers(0, 12, size=(650, 500))
        palette = ColorPalette(
            colors_rgb=np.random.default_rng(42).integers(0, 255, size=(12, 3), dtype=np.uint8)
        )
        generator = GridGenerator(columns=50, rows=65)
        grid = generator.generate(label_map, palette)

        for row in grid:
            for cell in row:
                assert len(cell.label) == 1
                assert cell.label in LABEL_CHARS[:12]

    def test_grid_labels_8_colors(self) -> None:
        """Given 8 colors, labels are 0–7."""
        label_map = np.random.default_rng(42).integers(0, 8, size=(130, 100))
        palette = ColorPalette(
            colors_rgb=np.random.default_rng(42).integers(0, 255, size=(8, 3), dtype=np.uint8)
        )
        generator = GridGenerator(columns=10, rows=13)
        grid = generator.generate(label_map, palette)

        all_labels = {cell.label for row in grid for cell in row}
        assert all_labels.issubset(set("01234567"))

    def test_grid_labels_20_colors(self) -> None:
        """Given 20 colors, labels are 0–9, A–J — all single character."""
        label_map = np.random.default_rng(42).integers(0, 20, size=(130, 100))
        palette = ColorPalette(
            colors_rgb=np.random.default_rng(42).integers(0, 255, size=(20, 3), dtype=np.uint8)
        )
        generator = GridGenerator(columns=10, rows=13)
        grid = generator.generate(label_map, palette)

        for row in grid:
            for cell in row:
                assert len(cell.label) == 1
                assert cell.label in LABEL_CHARS[:20]

    def test_grid_cell_coordinates(self) -> None:
        """Each cell should have correct row/col coordinates."""
        label_map = np.zeros((65, 50), dtype=int)
        palette = ColorPalette(colors_rgb=np.array([[0, 0, 0]], dtype=np.uint8))
        generator = GridGenerator(columns=50, rows=65)
        grid = generator.generate(label_map, palette)

        for r, row in enumerate(grid):
            for c, cell in enumerate(row):
                assert cell.row == r
                assert cell.col == c
