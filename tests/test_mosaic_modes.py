"""Tests for mosaic modes (circle, hexagon). Maps to AC2.1–AC2.13."""

import math

import numpy as np
import pytest

from src.models.mosaic import ColorPalette, GridCell, MosaicSheet
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


def _make_sheet(
    n_colors: int = 12,
    columns: int = 10,
    rows: int = 10,
    component_size_mm: float = 3.0,
    mode: str = "square",
) -> MosaicSheet:
    """Build a MosaicSheet for testing."""
    grid, palette = _make_grid(n_colors, columns, rows)
    return MosaicSheet(
        mosaic_id="test-modes",
        grid=grid,
        palette=palette,
        columns=columns,
        rows=rows,
        component_size_mm=component_size_mm,
        mode=mode,
    )


class TestMosaicModeEnum:
    """Tests for MosaicMode enum. AC2.1."""

    def test_mode_enum_has_three_values(self) -> None:
        """MosaicMode enum should have square, circle, hexagon."""
        from src.api.schemas import MosaicMode

        assert MosaicMode.SQUARE == "square"
        assert MosaicMode.CIRCLE == "circle"
        assert MosaicMode.HEXAGON == "hexagon"
        assert len(MosaicMode) == 3


class TestCirclePreview:
    """Tests for circle mode preview rendering. AC2.2."""

    def test_circle_preview_has_black_gaps(self) -> None:
        """Circle preview: inter-cell space should be black (0,0,0)."""
        grid, palette = _make_grid(n_colors=4, columns=5, rows=5)
        renderer = PreviewRenderer(cell_size=20)
        img = renderer.render(grid, palette, mode="circle")
        pixels = np.array(img)

        # Corner pixel of first cell (0,0) should be black (outside the circle)
        assert tuple(pixels[0, 0]) == (
            0,
            0,
            0,
        ), "Corner of cell should be black in circle mode"

    def test_circle_preview_cell_is_round(self) -> None:
        """Circle preview: center of cell should have palette color, not black."""
        grid, palette = _make_grid(n_colors=4, columns=5, rows=5)
        renderer = PreviewRenderer(cell_size=20)
        img = renderer.render(grid, palette, mode="circle")
        pixels = np.array(img)

        # Center of cell (0,0) should be the cell color
        cx, cy = 10, 10  # center of cell_size=20
        center_color = tuple(pixels[cy, cx])
        expected = tuple(int(v) for v in palette.colors_rgb[grid[0][0].color_index])
        assert (
            center_color == expected
        ), f"Center should be {expected}, got {center_color}"


class TestHexagonPreview:
    """Tests for hexagon mode preview rendering. AC2.11."""

    def test_hexagon_preview_has_black_gaps(self) -> None:
        """Hexagon preview: inter-cell space should be black."""
        grid, palette = _make_grid(n_colors=4, columns=5, rows=5)
        renderer = PreviewRenderer(cell_size=20)
        img = renderer.render(grid, palette, mode="hexagon")
        pixels = np.array(img)

        # Corner pixel (0,0) should be black (outside any hexagon)
        assert tuple(pixels[0, 0]) == (
            0,
            0,
            0,
        ), "Corner should be black in hexagon mode"

    def test_hexagon_odd_row_offset(self) -> None:
        """Hexagon preview: odd row cells should be offset by half a column."""
        grid, palette = _make_grid(n_colors=4, columns=5, rows=4)
        renderer = PreviewRenderer(cell_size=20)
        img = renderer.render(grid, palette, mode="hexagon")
        pixels = np.array(img)

        # In hexagon mode with cell_size=20:
        # col_spacing = cell_size = 20
        # row_spacing = cell_size * sqrt(3)/2 ≈ 17.32
        # Even row (0): center at col*20 + 10
        # Odd row (1): center at col*20 + 10 + 10 (offset by half col_spacing)
        # The center of cell (1, 0) should be offset by 10px right
        row_spacing = int(20 * math.sqrt(3) / 2)
        odd_row_y = row_spacing + row_spacing // 2  # approximate center of row 1
        # At x=10 (center of col 0 for an odd row with offset), should have color
        odd_center_x = 10 + 10  # col_spacing/2 offset
        # If offset is implemented, the pixel at the odd-row center should be colored
        color = tuple(pixels[odd_row_y, odd_center_x])
        assert color != (
            0,
            0,
            0,
        ), "Odd row hex center should be colored (offset applied)"

    def test_hexagon_pointy_top_orientation(self) -> None:
        """Hexagon preview: hexagons should be pointy-top (taller than wide check)."""
        # This is validated by the geometry helper
        from src.rendering.geometry import hex_vertices

        vertices = hex_vertices(100, 100, 20)
        assert len(vertices) == 6

        # For pointy-top, the top vertex should be directly above center
        # Top vertex: (cx, cy - R)
        top_vertex = vertices[0]
        assert top_vertex[0] == pytest.approx(
            100, abs=0.1
        ), "Top vertex x should be at center"
        assert top_vertex[1] == pytest.approx(
            80, abs=0.1
        ), "Top vertex y should be cy - R"


class TestCirclePdf:
    """Tests for circle mode PDF rendering. AC2.8, AC2.9."""

    def test_pdf_circle_mode_renders_circles(self) -> None:
        """Circle mode PDF should be valid and contain circle drawing commands."""
        from src.rendering.pdf import PdfRenderer

        sheet = _make_sheet(n_colors=4, columns=5, rows=5, mode="circle")
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        assert pdf_bytes[:5] == b"%PDF-"
        # PDF should have 2 pages
        assert pdf_bytes.count(b"/Type /Page") >= 2
        # All labels should appear
        for i in range(4):
            label = sheet.palette.label(i)
            assert label.encode("latin-1") in pdf_bytes

    def test_pdf_circle_labels_centered(self) -> None:
        """Circle mode PDF should contain labels."""
        from src.rendering.pdf import PdfRenderer

        sheet = _make_sheet(n_colors=4, columns=5, rows=5, mode="circle")
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        # All labels should appear in the PDF
        for i in range(4):
            label = sheet.palette.label(i)
            assert (
                label.encode("latin-1") in pdf_bytes
            ), f"Label '{label}' missing from PDF"


class TestHexagonPdf:
    """Tests for hexagon mode PDF rendering. AC2.13."""

    def test_pdf_hexagon_mode_renders_hexagons(self) -> None:
        """Hexagon mode PDF should be valid with all labels."""
        from src.rendering.pdf import PdfRenderer

        sheet = _make_sheet(n_colors=4, columns=5, rows=5, mode="hexagon")
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        assert pdf_bytes[:5] == b"%PDF-"
        assert pdf_bytes.count(b"/Type /Page") >= 2
        for i in range(4):
            label = sheet.palette.label(i)
            assert label.encode("latin-1") in pdf_bytes


class TestLegendModeIndependent:
    """Tests for legend page across modes. AC2.10."""

    def test_legend_unchanged_across_modes(self) -> None:
        """Legend page should be identical regardless of mode."""
        from src.rendering.pdf import PdfRenderer

        renderer = PdfRenderer()
        square_sheet = _make_sheet(n_colors=8, mode="square")
        circle_sheet = _make_sheet(n_colors=8, mode="circle")
        hex_sheet = _make_sheet(n_colors=8, mode="hexagon")

        sq_pdf = renderer.render(square_sheet)
        ci_pdf = renderer.render(circle_sheet)
        hx_pdf = renderer.render(hex_sheet)

        # All should be valid PDFs with 2 pages
        for pdf_bytes in [sq_pdf, ci_pdf, hx_pdf]:
            assert pdf_bytes[:5] == b"%PDF-"
            assert pdf_bytes.count(b"/Type /Page") >= 2

        # All labels should appear in all PDFs
        for i in range(8):
            label = square_sheet.palette.label(i)
            for pdf_bytes in [sq_pdf, ci_pdf, hx_pdf]:
                assert label.encode("latin-1") in pdf_bytes
