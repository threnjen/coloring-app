# 01: Component Size Selector — Plan

**Status**: Not Started
**Dependencies**: Phase 1 (complete)
**Blocked by**: None
**Blocks**: 02-mosaic-modes (uses dimension lookup table)

---

## Requirements & Traceability

### Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC2.3 | User can select component size: 3mm, 4mm, or 5mm |
| AC2.4 | Square/circle grid dimensions adjust correctly per size (60×80 at 3mm, 50×65 at 4mm, 40×52 at 5mm) |
| AC2.12 | Hexagon grid dimensions adjust per size (60×93 at 3mm, 45×70 at 4mm, 36×56 at 5mm) |

### Non-Goals

- No rendering changes (circle/hexagon rendering is in 02-mosaic-modes)
- No changes to the enhancement pipeline
- No color palette editing
- No mode toggle UI — only size selector
- Hexagon dimensions are *defined* here but not *rendered* until 02

### Traceability

| AC | Code Areas | Planned Tests |
|----|------------|---------------|
| AC2.3 | `src/config.py`, `src/api/schemas.py`, `src/api/routes.py`, `static/js/app.js`, `static/index.html` | `test_size_enum_values`, `test_process_accepts_size_param`, `test_process_rejects_invalid_size` |
| AC2.4 | `src/config.py`, `src/processing/grid.py`, `src/rendering/preview.py`, `src/rendering/pdf.py` | `test_grid_dimensions_3mm`, `test_grid_dimensions_4mm`, `test_grid_dimensions_5mm`, `test_pdf_layout_adjusts_per_size`, `test_preview_dimensions_adjust_per_size` |
| AC2.12 | `src/config.py` | `test_hex_dimensions_in_lookup_table` |

---

## Stage 0: Test Prerequisites

**Goal**: Verify existing test suite passes; plan new test cases
**Success Criteria**: All existing tests pass; new test stubs written and failing
**Status**: Not Started

- Run full test suite to confirm green baseline
- Write failing tests for `test_grid_dimensions_4mm`, `test_grid_dimensions_5mm` (currently only 3mm exists in `test_grid.py`)
- Write failing test for API accepting `size` parameter

## Stage 1: Config — Dimension Lookup Table + ComponentSize Enum

**Goal**: Add `ComponentSize` enum and `GRID_DIMENSIONS` lookup table to `config.py`
**Success Criteria**: Lookup table returns correct (cols, rows) for each size and mode combination; existing 3mm constants still work
**Status**: Not Started

### Design

Add to `src/config.py`:
- A `ComponentSize` enum with values `3`, `4`, `5`
- A `GRID_DIMENSIONS` dict keyed by `(size_mm, mode)` → `(columns, rows)`:
  - Square/circle: `(3, "square")` → (60, 80), `(4, "square")` → (50, 65), `(5, "square")` → (40, 52)
  - Hexagon: `(3, "hexagon")` → (60, 93), `(4, "hexagon")` → (45, 70), `(5, "hexagon")` → (36, 56)
  - Circle uses same dimensions as square
- Keep existing `GRID_COLUMNS`, `GRID_ROWS`, `COMPONENT_SIZE_MM` as defaults (backward compat)

### Correctness Notes

- Hexagon row count derivation: printable_height / (size × √3/2), rounded up
- Hexagon column count: printable_width / size (same column spacing as square for pointy-top)
- The 180mm × 240mm printable area comes from the 3mm × 60×80 baseline

## Stage 2: Parameterize GridGenerator

**Goal**: `GridGenerator` accepts size-derived columns/rows instead of only config defaults
**Success Criteria**: `GridGenerator(columns=50, rows=65)` produces correct grid; all existing tests still pass (they use defaults)
**Status**: Not Started

- `GridGenerator.__init__` already accepts `columns` and `rows` parameters — no change needed to the class itself
- Update `_run_pipeline` in `routes.py` to look up dimensions from `GRID_DIMENSIONS` based on request size
- Update `MosaicSheet` construction to carry the selected `component_size_mm`

## Stage 3: Update PDF + Preview Renderers for Dynamic Size

**Goal**: `PdfRenderer` and `PreviewRenderer` use the sheet's `component_size_mm` and dimensions for layout
**Success Criteria**: PDF grid fills correct printable area for each size; preview cell count matches grid dimensions
**Status**: Not Started

- `PdfRenderer._draw_grid_page` already reads `sheet.component_size_mm` and `sheet.columns`/`sheet.rows` — verify margins recalculate correctly for non-3mm sizes
- `PreviewRenderer.render` derives dimensions from `grid` shape — should adapt automatically
- Add test: generate PDF at 4mm, verify grid area = 50×4mm × 65×4mm = 200mm × 260mm

## Stage 4: API — Accept Size Parameter

**Goal**: `POST /api/process` accepts optional `size` parameter (3, 4, or 5)
**Success Criteria**: API validates size, passes it through pipeline, returns correct grid dimensions in response
**Status**: Not Started

- Add `size: int = Field(default=3, ge=3, le=5)` to `ProcessRequest` (or use `ComponentSize` enum)
- In `_run_pipeline`, look up `(size, "square")` in `GRID_DIMENSIONS` to get cols/rows
- Mode will default to `"square"` here — 02-mosaic-modes will add the mode parameter later

## Stage 5: UI — Size Dropdown

**Goal**: Add a size selector dropdown in the processing step
**Success Criteria**: User can select 3mm/4mm/5mm; selection is sent with process request; grid dimensions in response match selection
**Status**: Not Started

- Add `<select>` element to `index.html` in step 3 (alongside color count slider)
- Update `app.js` to include `size` in the `/api/process` request body
- Display selected size label (e.g., "3mm (60×80)" / "4mm (50×65)" / "5mm (40×52)")

---

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Size change after processing | Re-run full pipeline (grid generation uses quantized image, which depends on grid dimensions for downsampling) |
| Default when size omitted | Default to 3mm (backward compatible with Phase 1) |
| Invalid size value (e.g., 7) | API returns 400 with descriptive error |
| PDF margins for non-3mm sizes | Margins recalculate: `(paper_width - cols*size) / 2` |

## Clean Design Checklist

- [ ] Lookup table is a simple dict, not over-abstracted
- [ ] Existing Phase 1 behavior unchanged when size=3mm (default)
- [ ] No circular imports between config and models
- [ ] Enum values are the integer mm values (3, 4, 5), not strings

## Test Plan

### Unit Tests

| Test | AC |
|------|----|
| `test_grid_dimensions_3mm` | AC2.4 — 60×80 (already exists, verify still passes) |
| `test_grid_dimensions_4mm` | AC2.4 — 50×65 |
| `test_grid_dimensions_5mm` | AC2.4 — 40×52 |
| `test_dimension_lookup_square_all_sizes` | AC2.4 — lookup returns correct tuples |
| `test_dimension_lookup_hexagon_all_sizes` | AC2.12 — lookup returns correct tuples |
| `test_pdf_layout_4mm` | AC2.4 — grid area = 200mm × 260mm |
| `test_pdf_layout_5mm` | AC2.4 — grid area = 200mm × 260mm |

### Integration Tests

| Test | Description |
|------|----|
| `test_process_with_size_4mm` | POST /api/process with size=4 → response has columns=50, rows=65 |
| `test_process_with_size_5mm` | POST /api/process with size=5 → response has columns=40, rows=52 |
| `test_process_default_size` | POST /api/process without size → response has columns=60, rows=80 |
| `test_process_invalid_size` | POST /api/process with size=7 → 400/422 error |

### Top 3 Given/When/Then

1. **Given** the dimension lookup table, **When** queried with `(4, "square")`, **Then** returns `(50, 65)`.
2. **Given** a cropped image, **When** processed with `size=5`, **Then** the mosaic sheet has 40 columns and 52 rows, and the PDF grid area is 200mm × 260mm.
3. **Given** a process request with no `size` parameter, **When** processed, **Then** grid is 60×80 (3mm default), identical to Phase 1 behavior.
