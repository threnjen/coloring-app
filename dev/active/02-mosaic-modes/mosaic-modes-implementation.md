# Implementation Record: Mosaic Modes

## Summary
Added circle and hexagon mosaic rendering modes to the coloring app. Users can now choose between square (pixel), circle, and hexagon mosaic modes via a 3-way radio toggle. The mode flows through the API, affects preview rendering (with black inter-cell gaps for circle and hex), produces mode-aware PDFs, and uses a shared geometry helper for hexagon vertex computation.

## Acceptance Criteria Status

| AC | Description | Status | Implementing Files | Notes |
|----|-------------|--------|--------------------|-------|
| AC2.1 | User can choose between square, circle, hexagon modes | Done | `src/api/schemas.py`, `static/index.html`, `static/js/app.js` | MosaicMode enum + radio buttons |
| AC2.2 | Circle mode renders circles with black inter-cell space | Done | `src/rendering/preview.py` | Black bg + inscribed ellipse |
| AC2.8 | PDF respects selected mode | Done | `src/rendering/pdf.py` | Mode dispatch in _draw_grid_page |
| AC2.9 | Circle PDF renders circles with centered labels | Done | `src/rendering/pdf.py` | Uses c.circle() + centered drawString |
| AC2.10 | Legend page works for all three modes | Done | `src/rendering/pdf.py` | Legend is mode-independent, verified by test |
| AC2.11 | Hexagon mode renders pointy-top hexagons with offset grid | Done | `src/rendering/preview.py`, `src/rendering/geometry.py` | Odd-row offset, polygon rendering |
| AC2.13 | Hexagon PDF renders pointy-top hexagons with centered labels | Done | `src/rendering/pdf.py` | Uses beginPath/moveTo/lineTo path ops |

## Files Changed

### Source Files

| File | Change Type | What Changed | Why |
|------|-------------|--------------|-----|
| `src/api/schemas.py` | Modified | Added `MosaicMode` enum; added `mode` field to `ProcessRequest` and `ProcessResponse` | AC2.1: API must accept and return mode |
| `src/models/mosaic.py` | Modified | Added `mode: str = "square"` field to `MosaicSheet` | AC2.1: model carries mode through pipeline |
| `src/rendering/preview.py` | Modified | Extracted `_draw_square_cell`; added `_draw_circle_cell`, `_draw_hexagon_cell`; render() accepts mode param; black bg for non-square | AC2.2, AC2.11: shape-specific preview rendering |
| `src/rendering/pdf.py` | Modified | Extracted `_draw_square_cell`; added `_draw_circle_cell`, `_draw_hexagon_cell`; mode dispatch in `_draw_grid_page`; hex layout spacing; black bg | AC2.8, AC2.9, AC2.13: shape-specific PDF rendering |
| `src/rendering/geometry.py` | Created | `hex_vertices(cx, cy, circumradius)` — computes 6 pointy-top hex vertices | AC2.11, AC2.13: shared geometry helper |
| `src/api/routes.py` | Modified | `_run_pipeline` accepts mode; uses `(size, mode)` for dimension lookup; passes mode to sheet and renderer; response includes mode | AC2.1: mode flows through pipeline |
| `static/index.html` | Modified | Added 3-way radio buttons (Square/Circle/Hexagon) in step 3 | AC2.1: UI for mode selection |
| `static/js/app.js` | Modified | Sends mode in process request; updates size labels per mode | AC2.1: JS wiring |
| `static/css/style.css` | Modified | Added `.mode-control`, `.mode-options`, `.mode-option` styles | AC2.1: mode selector styling |

### Test Files

| File | Change Type | What Changed | Covers |
|------|-------------|--------------|--------|
| `tests/test_mosaic_modes.py` | Created | 10 unit tests: enum, circle preview, hexagon preview, circle PDF, hexagon PDF, legend across modes | AC2.1, AC2.2, AC2.8, AC2.9, AC2.10, AC2.11, AC2.13 |
| `tests/test_mosaic_modes_integration.py` | Created | 3 integration tests: circle pipeline, hexagon pipeline, palette preservation | AC2.1, AC2.8 |

## Test Results
- **Baseline**: 45 passed, 0 failed (before implementation)
- **Final**: 58 passed, 0 failed (after implementation)
- **New tests added**: 13
- **Regressions**: None

## Deviations from Plan
None — all stages implemented as planned.

## Gaps
None — all acceptance criteria implemented.

## Reviewer Focus Areas
- Hexagon geometry in `src/rendering/geometry.py` and its usage in both `preview.py` and `pdf.py` — verify pointy-top orientation and odd-row offset
- PDF circle/hexagon rendering in `src/rendering/pdf.py:_draw_circle_cell` and `_draw_hexagon_cell` — verify label centering and black background
- Mode parameter flow through `routes.py:_run_pipeline` → `MosaicSheet` → renderers — ensure no mode leaks or defaults to wrong value
- Preview hexagon image sizing in `preview.py:render()` — hex grids compute different width/height than square grids
- Integration test coverage: `test_mosaic_modes_integration.py` tests full pipeline for circle and hexagon modes
