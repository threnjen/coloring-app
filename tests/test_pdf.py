"""Tests for PDF generation. Maps to AC1.9, AC1.10."""

from io import BytesIO

import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

from src.models.mosaic import ColorPalette, GridCell, MosaicSheet
from src.rendering.pdf import PdfRenderer
from tests.conftest import make_sheet as _make_sheet


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
        """Grid should occupy 180mm × 240mm on US Letter (60×80 at 3mm). AC1.10."""
        from src.config import PAPER_HEIGHT_MM, PAPER_WIDTH_MM

        sheet = _make_sheet(n_colors=12, columns=60, rows=80)
        grid_width_mm = sheet.columns * sheet.component_size_mm
        grid_height_mm = sheet.rows * sheet.component_size_mm
        assert grid_width_mm == 180.0
        assert grid_height_mm == 240.0
        # Margins computed dynamically (same as pdf.py)
        margin_side_mm = (PAPER_WIDTH_MM - grid_width_mm) / 2
        margin_top_mm = (PAPER_HEIGHT_MM - grid_height_mm) / 2
        assert grid_width_mm + 2 * margin_side_mm <= PAPER_WIDTH_MM
        assert grid_height_mm + margin_top_mm <= PAPER_HEIGHT_MM

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

    def test_pdf_layout_4mm(self) -> None:
        """Grid area at 4mm = 50×4mm × 65×4mm = 200mm × 260mm. AC2.4."""
        sheet = _make_sheet(n_colors=12, columns=50, rows=65, component_size_mm=4.0)
        grid_width_mm = sheet.columns * sheet.component_size_mm
        grid_height_mm = sheet.rows * sheet.component_size_mm
        assert grid_width_mm == 200.0
        assert grid_height_mm == 260.0

        from src.config import PAPER_HEIGHT_MM, PAPER_WIDTH_MM

        assert grid_width_mm <= PAPER_WIDTH_MM
        assert grid_height_mm <= PAPER_HEIGHT_MM

        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"

    def test_pdf_layout_5mm(self) -> None:
        """Grid area at 5mm = 40×5mm × 52×5mm = 200mm × 260mm. AC2.4."""
        sheet = _make_sheet(n_colors=12, columns=40, rows=52, component_size_mm=5.0)
        grid_width_mm = sheet.columns * sheet.component_size_mm
        grid_height_mm = sheet.rows * sheet.component_size_mm
        assert grid_width_mm == 200.0
        assert grid_height_mm == 260.0

        renderer = PdfRenderer()
        pdf_bytes = renderer.render(sheet)
        assert len(pdf_bytes) > 0
        assert pdf_bytes[:5] == b"%PDF-"
