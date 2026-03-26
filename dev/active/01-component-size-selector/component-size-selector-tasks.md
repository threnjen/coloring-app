# 01: Component Size Selector — Tasks

## Stage 0: Test Prerequisites
- [ ] Run full test suite — confirm all green
- [ ] Write `test_grid_dimensions_4mm` (red)
- [ ] Write `test_grid_dimensions_5mm` (red)
- [ ] Write `test_dimension_lookup_square_all_sizes` (red)
- [ ] Write `test_dimension_lookup_hexagon_all_sizes` (red)
- [ ] Write `test_process_with_size_4mm` integration test (red)
- [ ] Write `test_process_invalid_size` integration test (red)

## Stage 1: Config — Lookup Table + Enum
- [ ] Add `GRID_DIMENSIONS` dict to `src/config.py`
- [ ] Include square entries: (3→60×80), (4→50×65), (5→40×52)
- [ ] Include hexagon entries: (3→60×93), (4→45×70), (5→36×56)
- [ ] Include circle entries (same as square)
- [ ] Verify `test_dimension_lookup_*` tests pass (green)
- [ ] Verify all existing tests still pass

## Stage 2: Parameterize Pipeline
- [ ] Update `_run_pipeline` in `src/api/routes.py` to accept `size` parameter
- [ ] Look up `(size, "square")` in `GRID_DIMENSIONS` for cols/rows
- [ ] Pass looked-up cols/rows to `GridGenerator`
- [ ] Pass `component_size_mm=size` to `MosaicSheet`
- [ ] Verify `test_grid_dimensions_4mm` and `5mm` pass (green)
- [ ] Verify existing `test_grid_dimensions_3mm` still passes

## Stage 3: PDF + Preview Layout
- [ ] Verify `PdfRenderer._draw_grid_page` recalculates margins from sheet dimensions (no code change expected — it already reads from sheet)
- [ ] Add `test_pdf_layout_4mm` — verify grid area dimensions
- [ ] Verify `PreviewRenderer.render` adapts automatically (no code change expected)
- [ ] Run full test suite — all green

## Stage 4: API Schema Update
- [ ] Add `size: int` field to `ProcessRequest` in `src/api/schemas.py` (default=3, ge=3, le=5)
- [ ] Update `process_image` in `src/api/routes.py` to pass `req.size` through
- [ ] Update `ProcessResponse` to include `component_size_mm` field
- [ ] Verify `test_process_with_size_4mm` passes (green)
- [ ] Verify `test_process_default_size` passes (green — omitted size defaults to 3)
- [ ] Verify `test_process_invalid_size` passes (green — returns 422)

## Stage 5: UI — Size Dropdown
- [ ] Add `<select id="size-select">` to `static/index.html` in step 3 section
- [ ] Options: "3mm (60×80)", "4mm (50×65)", "5mm (40×52)"
- [ ] Update `static/js/app.js` process handler to include `size` in request body
- [ ] Add DOM reference for size select element
- [ ] Manual QA: verify size changes produce different grid densities

## Final
- [ ] Run full test suite — all green
- [ ] Review: no debug code, no TODOs without issue numbers
- [ ] Commit with message: `feat: add component size selector (3mm/4mm/5mm)`
