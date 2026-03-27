"""Tests for preview rendering. Maps to AC1.8."""

import numpy as np

from src.models.mosaic import ColorPalette
from src.models.mosaic import GridCell
from src.rendering.preview import PREVIEW_CELL_PX
from src.rendering.preview import PreviewRenderer


def _make_grid(
    n_colors: int, columns: int, rows: int
) -> tuple[list[list[GridCell]], ColorPalette]:
    """Build a simple grid and palette for testing."""
    palette = ColorPalette(
        colors_rgb=np.random.default_rng(42).integers(
            0, 255, size=(n_colors, 3), dtype=np.uint8
        )
    )
    grid = []
    for r in range(rows):
        row_cells = []
        for c in range(columns):
            idx = (r * columns + c) % n_colors
            row_cells.append(
                GridCell(row=r, col=c, color_index=idx, label=palette.label(idx))
            )
        grid.append(row_cells)
    return grid, palette


class TestPreviewRenderer:
    """Tests for the PreviewRenderer class."""

    def test_preview_dimensions(self) -> None:
        """Preview image should be cols*cell_px × rows*cell_px."""
        grid, palette = _make_grid(n_colors=8, columns=60, rows=80)
        renderer = PreviewRenderer(cell_size=PREVIEW_CELL_PX)
        img = renderer.render(grid, palette)

        assert img.width == 60 * PREVIEW_CELL_PX
        assert img.height == 80 * PREVIEW_CELL_PX

    def test_preview_is_rgb(self) -> None:
        """Preview image should be in RGB mode."""
        grid, palette = _make_grid(n_colors=8, columns=10, rows=10)
        renderer = PreviewRenderer()
        img = renderer.render(grid, palette)
        assert img.mode == "RGB"

    def test_preview_colors_match_palette(self) -> None:
        """Each cell's background color should match its palette color."""
        n_colors = 4
        cell_size = 20
        grid, palette = _make_grid(n_colors=n_colors, columns=10, rows=10)
        renderer = PreviewRenderer(cell_size=cell_size)
        img = renderer.render(grid, palette)
        pixels = np.array(img)

        for i in range(n_colors):
            expected = tuple(int(v) for v in palette.colors_rgb[i])
            # Find a cell with this color and sample a corner pixel (avoids label text)
            for row_cells in grid:
                for cell in row_cells:
                    if cell.color_index == i:
                        px = cell.col * cell_size + 1
                        py = cell.row * cell_size + 1
                        actual = tuple(pixels[py, px])
                        assert (
                            actual == expected
                        ), f"Color {i}: expected {expected}, got {actual}"
                        break
                else:
                    continue
                break
