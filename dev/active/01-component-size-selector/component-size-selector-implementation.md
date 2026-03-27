# Implementation Record: Component Size Selector

## Summary
Added component size selector (3mm/4mm/5mm) to the mosaic coloring app. Users can select a size via a dropdown in the UI, which changes grid dimensions accordingly. A `GRID_DIMENSIONS` lookup table in config maps `(size, mode)` to `(columns, rows)` for square, circle, and hexagon modes. The API, pipeline, and PDF renderer all dynamically adapt to the selected size.

## Acceptance Criteria Status

| AC | Description | Status | Implementing Files | Notes |
|----|-------------|--------|--------------------|-------|
| AC2.3 | User can select component size: 3mm, 4mm, or 5mm | Done | `src/config.py`, `src/api/schemas.py`, `static/index.html`, `static/js/app.js` | Dropdown in UI, validated by Pydantic schema (ge=3, le=5) |
| AC2.4 | Square/circle grid dimensions adjust correctly per size | Done | `src/config.py`, `src/api/routes.py`, `src/rendering/pdf.py` | Lookup table returns correct (cols, rows); pipeline and PDF use dynamic dimensions |
| AC2.12 | Hexagon grid dimensions adjust per size | Done | `src/config.py` | Defined in lookup table; rendering deferred to 02-mosaic-modes |

## Files Changed

### Source Files

| File | Change Type | What Changed | Why |
|------|-------------|--------------|-----|
| `src/config.py` | Modified | Added `GRID_DIMENSIONS` lookup dict with entries for square/circle/hexagon at 3/4/5mm | AC2.3, AC2.4, AC2.12: central dimension configuration |
| `src/api/schemas.py` | Modified | Added `size: int` field to `ProcessRequest` (default=3, ge=3, le=5); added `component_size_mm: float` to `ProcessResponse` | AC2.3: API accepts and returns size |
| `src/api/routes.py` | Modified | `_run_pipeline` accepts `size` param, looks up dimensions from `GRID_DIMENSIONS`; `process_image` passes `req.size`; response uses sheet dimensions | AC2.4: pipeline uses dynamic dimensions |
| `src/rendering/pdf.py` | Modified | `_draw_grid_page` calculates margins dynamically from sheet dimensions instead of hardcoded constants | AC2.4: PDF layout adapts to grid size |
| `static/index.html` | Modified | Added `<select id="size-select">` with 3mm/4mm/5mm options in step 3 | AC2.3: UI size selector |
| `static/js/app.js` | Modified | Added `sizeSelect` DOM reference; included `size` in process request body | AC2.3: sends size to API |
| `static/css/style.css` | Modified | Added `.size-control` styles matching existing `.color-control` pattern | AC2.3: consistent UI styling |

### Test Files

| File | Change Type | What Changed | Covers |
|------|-------------|--------------|--------|
| `tests/test_grid.py` | Modified | Added `test_grid_dimensions_4mm`, `test_grid_dimensions_5mm`, `TestDimensionLookup` class with 3 tests | AC2.4, AC2.12 |
| `tests/test_integration.py` | Modified | Added `test_process_with_size_4mm`, `test_process_with_size_5mm`, `test_process_default_size`, `test_process_invalid_size` | AC2.3, AC2.4 |
| `tests/test_pdf.py` | Modified | Added `test_pdf_layout_4mm`, `test_pdf_layout_5mm` | AC2.4 |

## Test Results
- **Baseline**: 34 passed, 0 failed (before implementation)
- **Final**: 45 passed, 0 failed (after implementation)
- **New tests added**: 11
- **Regressions**: None

## Deviations from Plan
None

## Gaps
None

## Reviewer Focus Areas
- Dimension lookup table in `src/config.py:33-50` — verify all 9 entries match the reference table in context doc
- Dynamic margin calculation in `src/rendering/pdf.py:_draw_grid_page` — replaced hardcoded `MARGIN_SIDE_MM`/`MARGIN_TOP_MM` with computed values from sheet dimensions
- Pydantic validation in `src/api/schemas.py` uses `ge=3, le=5` — only allows integer sizes 3, 4, 5 (size=2 or size=6 rejected)
- `_run_pipeline` always uses `"square"` mode for lookup — hexagon/circle mode selection deferred to 02-mosaic-modes
