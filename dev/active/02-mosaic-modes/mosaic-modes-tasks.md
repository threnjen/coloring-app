# 02: Mosaic Modes — Tasks

**Prerequisite**: 01-component-size-selector must be complete.

## Stage 0: Test Prerequisites
- [ ] Write `test_mode_enum_has_three_values` (red)
- [ ] Write `test_circle_preview_has_black_gaps` (red) — render circle preview, check black pixels between cells
- [ ] Write `test_hexagon_preview_has_black_gaps` (red)
- [ ] Write `test_hexagon_odd_row_offset` (red) — verify odd-row cells are offset
- [ ] Write `test_pdf_circle_mode_renders_circles` (red) — PDF stream contains circle commands
- [ ] Write `test_pdf_hexagon_mode_renders_hexagons` (red) — PDF stream contains path commands
- [ ] Write integration `test_pipeline_circle_mode` (red)
- [ ] Write integration `test_pipeline_hexagon_mode` (red)

## Stage 1: MosaicMode Enum + Model
- [ ] Add `MosaicMode` str enum to `src/api/schemas.py` with values `square`, `circle`, `hexagon`
- [ ] Add `mode: str = "square"` to `MosaicSheet` dataclass
- [ ] Verify `test_mode_enum_has_three_values` passes (green)
- [ ] Verify all existing tests still pass

## Stage 2: Extract Square Rendering
- [ ] In `PreviewRenderer.render`, extract cell drawing body to `_draw_square_cell(self, draw, cell, x0, y0, palette, font)`
- [ ] Add mode dispatch: `if mode == "square": self._draw_square_cell(...)` 
- [ ] In `PdfRenderer._draw_grid_page`, extract cell drawing to `_draw_square_cell(self, c, cell, x, y, cell_pt, font_name, font_size)`
- [ ] Add mode dispatch in `_draw_grid_page`
- [ ] Run all existing tests — must pass (pure refactor)

## Stage 3: Circle Rendering
- [ ] `PreviewRenderer._draw_circle_cell` — draw filled ellipse inscribed in cell with 1px gap, on black bg
- [ ] Update `PreviewRenderer.render` to fill background black when mode != "square"
- [ ] Label centering inside circle (same as square — text bbox center)
- [ ] `PdfRenderer._draw_circle_cell` — use `c.circle(cx, cy, radius)` with fill
- [ ] Update `PdfRenderer._draw_grid_page` to draw black background rect for circle mode
- [ ] Label centering inside circle in PDF
- [ ] Verify `test_circle_preview_has_black_gaps` passes (green)
- [ ] Verify `test_pdf_circle_mode_renders_circles` passes (green)

## Stage 4: Hexagon Rendering
- [ ] Create `src/rendering/geometry.py` with `hex_vertices(cx, cy, circumradius)` → list of 6 (x, y) tuples
- [ ] `PreviewRenderer._draw_hexagon_cell` — compute center with offset, draw filled polygon
- [ ] Handle odd-row x-offset: `x_center += col_spacing / 2` when `row % 2 == 1`
- [ ] Update `PreviewRenderer.render` for hex: use hex grid dimensions, hex row spacing
- [ ] `PdfRenderer._draw_hexagon_cell` — `beginPath`/`moveTo`/`lineTo`/`closePath`/`fillPath`
- [ ] Label centering at hex center in PDF
- [ ] Verify `test_hexagon_preview_has_black_gaps` passes (green)
- [ ] Verify `test_hexagon_odd_row_offset` passes (green)
- [ ] Verify `test_pdf_hexagon_mode_renders_hexagons` passes (green)

## Stage 5: API — Mode Parameter
- [ ] Add `mode: MosaicMode = MosaicMode.SQUARE` to `ProcessRequest`
- [ ] Update `_run_pipeline` to accept mode, use `(size, mode.value)` for dimension lookup
- [ ] Store mode in `MosaicSheet`
- [ ] `PreviewRenderer.render` reads mode from method parameter or sheet
- [ ] `PdfRenderer._draw_grid_page` reads mode from `sheet.mode`
- [ ] Update `ProcessResponse` to include `mode` field
- [ ] Verify integration tests pass (green)

## Stage 6: UI — Mode Toggle
- [ ] Add radio buttons to `static/index.html` in step 3: Square / Circle / Hexagon
- [ ] Default: Square selected
- [ ] Update `static/js/app.js` to read selected mode and include in request body
- [ ] Update size dropdown labels to show correct dimensions per mode (hex has different rows)
- [ ] Add CSS styles for mode selector in `static/css/style.css`
- [ ] Manual QA: process image in each mode, verify preview and PDF

## Final
- [ ] Run full test suite — all green
- [ ] Review: no stale square-only assumptions
- [ ] Commit with message: `feat: add circle and hexagon mosaic modes`
