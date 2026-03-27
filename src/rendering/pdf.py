"""PDF generation: grid page + legend page on US Letter paper."""

import logging
from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from src.config import PAPER_HEIGHT_MM
from src.config import PAPER_WIDTH_MM
from src.models.mosaic import ColorPalette
from src.models.mosaic import GridCell
from src.models.mosaic import MosaicSheet

logger = logging.getLogger(__name__)


class PdfRenderer:
    """Generates a two-page PDF: grid page + legend page."""

    def render(self, sheet: MosaicSheet) -> bytes:
        """Generate a PDF for the mosaic sheet.

        Args:
            sheet: Complete mosaic sheet data.

        Returns:
            PDF file contents as bytes.
        """
        logger.info(
            "Rendering PDF for mosaic %s (%dx%d, %d colors)",
            sheet.mosaic_id,
            sheet.columns,
            sheet.rows,
            sheet.palette.count,
        )
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)

        self._draw_grid_page(c, sheet)
        c.showPage()
        self._draw_legend_page(c, sheet)
        c.showPage()

        c.save()
        return buf.getvalue()

    def _draw_grid_page(self, c: canvas.Canvas, sheet: MosaicSheet) -> None:
        """Draw the numbered grid on page 1."""
        page_w, page_h = letter
        cell_mm = sheet.component_size_mm
        cell_pt = cell_mm * mm

        grid_width_mm = sheet.columns * cell_mm
        grid_height_mm = sheet.rows * cell_mm
        margin_side_mm = (PAPER_WIDTH_MM - grid_width_mm) / 2
        margin_top_mm = (PAPER_HEIGHT_MM - grid_height_mm) / 2

        x_offset = margin_side_mm * mm
        y_top = page_h - margin_top_mm * mm

        font_name = "Helvetica"
        font_size = max(4, cell_mm * 0.6) * mm / mm * 2
        c.setFont(font_name, font_size)

        for row_cells in sheet.grid:
            for cell in row_cells:
                x = x_offset + cell.col * cell_pt
                y = y_top - (cell.row + 1) * cell_pt

                # Draw cell border
                c.setStrokeColorRGB(0.7, 0.7, 0.7)
                c.setLineWidth(0.25)
                c.rect(x, y, cell_pt, cell_pt)

                # Draw label centered in cell
                c.setFillColorRGB(0, 0, 0)
                tw = c.stringWidth(cell.label, font_name, font_size)
                tx = x + (cell_pt - tw) / 2
                ty = y + (cell_pt - font_size * 0.7) / 2
                c.drawString(tx, ty, cell.label)

    def _draw_legend_page(self, c: canvas.Canvas, sheet: MosaicSheet) -> None:
        """Draw the color legend on page 2."""
        page_w, page_h = letter
        palette = sheet.palette

        c.setFont("Helvetica-Bold", 16)
        c.drawString(30 * mm, page_h - 25 * mm, "Color Legend")

        swatch_size = 10 * mm
        row_height = 14 * mm
        x_start = 30 * mm
        y_start = page_h - 45 * mm
        cols_per_row = 4
        col_width = 42 * mm

        c.setFont("Helvetica", 11)

        for i in range(palette.count):
            col = i % cols_per_row
            row = i // cols_per_row
            x = x_start + col * col_width
            y = y_start - row * row_height

            # Draw color swatch
            r, g, b = (int(v) / 255.0 for v in palette.colors_rgb[i])
            c.setFillColorRGB(r, g, b)
            c.setStrokeColorRGB(0, 0, 0)
            c.setLineWidth(0.5)
            c.rect(x, y - swatch_size, swatch_size, swatch_size, fill=1)

            # Draw label next to swatch
            c.setFillColorRGB(0, 0, 0)
            label = palette.label(i)
            hex_color = palette.hex_color(i)
            c.drawString(
                x + swatch_size + 3 * mm,
                y - swatch_size + 3 * mm,
                f"{label}  {hex_color}",
            )
