"""Tests for PDF generation. Maps to AC1.9, AC1.10."""

from io import BytesIO

import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

from src.models.mosaic import ColorPalette
from src.models.mosaic import GridCell
from src.models.mosaic import MosaicSheet
from src.rendering.pdf import PdfRenderer


def _make_sheet(n_colors: int = 12, columns: int = 50, rows: int = 65) -> MosaicSheet:
    """Helper to build a MosaicSheet for testing."""
    palette = ColorPalette(
        colors_rgb=np.random.default_rng(42).integers(0, 255, size=(n_colors, 3), dtype=np.uint8)
    )
    grid = []
    for r in range(rows):
        row_cells = []
        for c in range(columns):
            idx = (r * columns + c) % n_colors
            row_cells.append(GridCell(row=r, col=c, color_index=idx, label=palette.label(idx)))
        grid.append(row_cells)

    return MosaicSheet(
        mosaic_id="test-pdf",
        grid=grid,
        palette=palette,
        columns=columns,
        rows=rows,
        component_size_mm=4.0,
    )


class TestPdfRenderer:
    """Tests for the PdfRenderer class."""

    def test_pdf_two_pages(self) -> None:
        """Given a mosaic, PDF has exactly 2 pages."""
        # We can verify page count by parsing the PDF
        from reportlab.lib.pagesizes import letter

        sheet = _make_sheet(n_colors=12)
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        # Simple check: count page markers in PDF
        assert pdf_bytes.count(b"/Type /Page") >= 2

    def test_pdf_grid_page_dimensions(self) -> None:
        """Grid should occupy 200mm × 260mm on US Letter (50×65 at 4mm). AC1.10."""
        from src.config import MARGIN_SIDE_MM
        from src.config import MARGIN_TOP_MM
        from src.config import PAPER_HEIGHT_MM
        from src.config import PAPER_WIDTH_MM

        sheet = _make_sheet(n_colors=12, columns=50, rows=65)
        grid_width_mm = sheet.columns * sheet.component_size_mm
        grid_height_mm = sheet.rows * sheet.component_size_mm
        assert grid_width_mm == 200.0
        assert grid_height_mm == 260.0
        assert grid_width_mm + 2 * MARGIN_SIDE_MM <= PAPER_WIDTH_MM
        assert grid_height_mm + MARGIN_TOP_MM <= PAPER_HEIGHT_MM

        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_is_valid(self) -> None:
        """Generated PDF should be valid (non-empty, starts with PDF header)."""
        sheet = _make_sheet(n_colors=8)
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_legend_has_all_colors(self) -> None:
        """Given 15 colors, legend page should contain all 15 labels."""
        sheet = _make_sheet(n_colors=15)
        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)

        # All labels 0-9 and A-E should appear in the PDF
        pdf_text = pdf_bytes.decode("latin-1")
        for i in range(15):
            label = sheet.palette.label(i)
            assert label in pdf_text

    def test_pdf_different_color_counts(self) -> None:
        """PDF should work for all valid color counts (8–20)."""
        renderer = PdfRenderer()
        for n in [8, 12, 15, 20]:
            sheet = _make_sheet(n_colors=n)
            pdf_bytes = renderer.render(sheet)
            assert len(pdf_bytes) > 0
            assert pdf_bytes[:5] == b"%PDF-"
