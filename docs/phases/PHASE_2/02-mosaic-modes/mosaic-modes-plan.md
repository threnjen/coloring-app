# 02: Mosaic Modes — Plan

**Status**: Not Started
**Dependencies**: 01-component-size-selector (dimension lookup table, parameterized pipeline)
**Blocked by**: 01-component-size-selector
**Blocks**: 04-color-palette-editor (palette re-render needs mode-aware preview)

---

## Requirements & Traceability

### Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC2.1 | User can choose between square (pixel), circle, and hexagon mosaic modes |
| AC2.2 | Circle mode renders circles in a grid with black inter-cell space (not touching) |
| AC2.8 | PDF output respects the selected mode (square, circle, or hexagon) and component size |
| AC2.9 | Circle mode PDF renders circles with labels centered inside each circle |
| AC2.10 | Legend page works correctly for all three modes |
| AC2.11 | Hexagon mode renders pointy-top hexagons in an offset grid with black inter-cell space |
| AC2.13 | Hexagon mode PDF renders pointy-top hexagons with labels centered inside each hexagon |

### Non-Goals

- No size selector changes (done in 01)
- No enhancement changes (done in 03)
- No color palette editing (done in 04)
- No separate `grid_circle.py` / `grid_hexagon.py` files — shape rendering lives in `PreviewRenderer` and `PdfRenderer`

### Traceability

| AC | Code Areas | Planned Tests |
|----|------------|---------------|
| AC2.1 | `src/config.py`, `src/api/schemas.py`, `src/api/routes.py`, `static/js/app.js` | `test_mode_enum_values`, `test_process_accepts_mode_param` |
| AC2.2 | `src/rendering/preview.py` | `test_circle_preview_has_black_gaps` |
| AC2.8 | `src/rendering/pdf.py` | `test_pdf_circle_mode`, `test_pdf_hexagon_mode` |
| AC2.9 | `src/rendering/pdf.py` | `test_pdf_circle_labels_centered` |
| AC2.10 | `src/rendering/pdf.py` | `test_legend_works_all_modes` |
| AC2.11 | `src/rendering/preview.py` | `test_hexagon_preview_has_black_gaps`, `test_hexagon_odd_row_offset`, `test_hexagon_pointy_top_orientation` |
| AC2.13 | `src/rendering/pdf.py` | `test_pdf_hexagon_mode_renders_hexagons` |

---

## Stage 0: Test Prerequisites

**Goal**: Write failing tests for all new rendering behaviors
**Success Criteria**: New tests written, all fail (red); existing tests still pass
**Status**: Not Started

## Stage 1: MosaicMode Enum + Model Update

**Goal**: Add `MosaicMode` enum; update `MosaicSheet` to carry mode
**Success Criteria**: Enum has three values; `MosaicSheet` has a `mode` field defaulting to `"square"`
**Status**: Not Started

### Design

- Add `MosaicMode` as a `str` enum to `src/api/schemas.py`: `square`, `circle`, `hexagon`
- Add `mode: str = "square"` field to `MosaicSheet` dataclass in `src/models/mosaic.py`
- The dimension lookup in `_run_pipeline` (from 01) now uses `(size, mode)` instead of `(size, "square")`

## Stage 2: Extract Square Rendering

**Goal**: Refactor `PreviewRenderer.render` and `PdfRenderer._draw_grid_page` so square drawing is an explicit internal method
**Success Criteria**: All existing tests still pass (pure refactor)
**Status**: Not Started

### Design

- `PreviewRenderer`: extract cell drawing loop body into `_draw_square_cell(draw, cell, palette, font)`
- `PdfRenderer._draw_grid_page`: extract cell drawing into `_draw_square_cell(c, cell, cell_pt, ...)`
- Main `render` / `_draw_grid_page` dispatches to `_draw_*_cell` based on `mode`

## Stage 3: Circle Rendering

**Goal**: Implement circle rendering in both preview and PDF
**Success Criteria**: Circle preview shows colored circles with black gaps and centered labels; circle PDF uses circular drawing commands
**Status**: Not Started

### Design — Preview

- `_draw_circle_cell`: draw filled circle (ellipse) inscribed in cell bounds with gap, on black background
- Gap = 1px in preview (proportional to cell_size)
- Background: fill image with black before drawing cells (instead of white)
- Label centered inside circle using same text logic as square

### Design — PDF

- `PdfRenderer._draw_circle_cell`: use `c.circle(cx, cy, radius)` from reportlab
- Fill with cell color, no stroke (black background fills gaps)
- Label `c.drawString` centered at `(cx, cy)`
- Page background: draw a black filled rect covering the grid area before drawing circles

### Correctness

- Circle diameter = `cell_size - gap` where gap = 0.5mm
- At 4mm: diameter = 3.5mm, radius = 1.75mm
- Labels must fit inside 3.5mm circle — use same font scaling as square (font_size = max(4, cell_mm * 0.6))

## Stage 4: Hexagon Rendering

**Goal**: Implement pointy-top hexagon rendering in both preview and PDF
**Success Criteria**: Hexagon preview shows colored pointy-top hexagons with offset rows and black gaps; hexagon PDF uses path-based hexagon drawing
**Status**: Not Started

### Design — Geometry (pointy-top)

For a regular hexagon with flat-to-flat distance `d` (= component_size - gap):
- Vertex-to-vertex distance = `d / cos(30°)` = `d × 2/√3`
- 6 vertices at angles 0°, 60°, 120°, 180°, 240°, 300° (starting from top)
- Column spacing = `component_size` (flat-to-flat)
- Row spacing = `component_size × √3/2`
- Odd rows offset by `component_size / 2` horizontally

### Design — Preview

- `_draw_hexagon_cell`: compute 6 vertices, draw filled polygon via `ImageDraw.polygon()`
- Background: fill image with black
- Label centered inside hex using bounding box center
- Grid dimensions: use hexagon lookup from `GRID_DIMENSIONS` (set up in 01)

### Design — PDF

- `PdfRenderer._draw_hexagon_cell`: use `c.beginPath()` / `c.moveTo()` / `c.lineTo()` / `c.closePath()` / `c.fillPath()`
- 6 vertices computed from center + angle
- Fill with cell color; black background rect drawn first
- Label centered at hex center

### Correctness

- Offset applies to odd rows (row index % 2 == 1)
- Edge clipping: hexagons on offset rows may extend slightly past the right edge — allow overshoot within margin
- At 3mm, inscribed circle of hex ≈ 2.6mm — labels may be tight with 20 colors, but this is deferred for visual QA per user decision

## Stage 5: API — Mode Parameter

**Goal**: `POST /api/process` accepts `mode` parameter
**Success Criteria**: Mode is validated, passed through pipeline, stored in `MosaicSheet`, and used for rendering
**Status**: Not Started

- Add `mode: str = "square"` to `ProcessRequest` (validated against `MosaicMode` enum)
- Pass `mode` to `_run_pipeline`
- `_run_pipeline` uses `(size, mode)` for dimension lookup (circle uses same dims as square)
- `MosaicSheet` stores the mode
- `PreviewRenderer.render` and `PdfRenderer._draw_grid_page` dispatch by `sheet.mode` / mode parameter

## Stage 6: UI — Mode Toggle

**Goal**: Add a 3-way mode selector in the processing step
**Success Criteria**: User can pick Square/Circle/Hexagon; selection sent with process request; preview renders in chosen mode
**Status**: Not Started

- Add radio buttons or segmented control to `index.html` in step 3
- Options: Square (default), Circle, Hexagon
- Update `app.js` to include `mode` in `/api/process` request body
- Size dropdown labels should update to show correct dimensions per mode (square/circle share dims; hexagon has different row counts)

---

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Circle at 3mm with 20 colors | Font size ~3.6pt inside 2.5mm circle — tight but legible for single chars |
| Hexagon at 3mm with 20 colors | Font inside ~2.6mm inscribed circle — may need visual QA |
| Mode switch after processing | Re-render only (grid data is mode-independent); palette unchanged |
| Legend page | Legend is mode-independent (just swatches + labels); no changes needed |
| PDF page background for circle/hex | Draw black rect first, then shapes on top |

## Clean Design Checklist

- [ ] No separate `grid_circle.py` / `grid_hexagon.py` — rendering in preview.py and pdf.py
- [ ] Grid generation (`processing/grid.py`) unchanged — shapes only affect rendering
- [ ] Hex vertex math in a shared helper or duplicated between preview/pdf? → shared `_hex_vertices(cx, cy, size)` utility function in a small `src/rendering/geometry.py`
- [ ] `MosaicMode` enum used consistently (API schema, model, config)

## Test Plan

### Unit Tests

| Test | AC |
|------|----|
| `test_circle_preview_has_black_gaps` | AC2.2 |
| `test_circle_preview_cell_is_round` | AC2.2 |
| `test_hexagon_preview_has_black_gaps` | AC2.11 |
| `test_hexagon_odd_row_offset` | AC2.11 |
| `test_hexagon_pointy_top_orientation` | AC2.11 |
| `test_pdf_circle_mode_renders_circles` | AC2.9 |
| `test_pdf_hexagon_mode_renders_hexagons` | AC2.13 |
| `test_legend_unchanged_across_modes` | AC2.10 |
| `test_mode_enum_has_three_values` | AC2.1 |

### Integration Tests

| Test | Description |
|------|----|
| `test_pipeline_circle_mode` | Full pipeline with mode=circle → PDF has circles |
| `test_pipeline_hexagon_mode` | Full pipeline with mode=hexagon → PDF has hex paths |
| `test_mode_switch_preserves_palette` | Process as square → reprocess as circle → same palette |

### Top 3 Given/When/Then

1. **Given** a processed mosaic at 4mm square, **When** reprocessed with mode=circle, **Then** preview shows circles with black gaps, same colors and labels.
2. **Given** a 4mm hexagon mosaic, **When** PDF generated, **Then** PDF stream contains `moveTo`/`lineTo` path commands forming hexagonal shapes, and labels are centered.
3. **Given** any mode, **When** PDF generated, **Then** legend page is identical (same swatches, same labels, same layout).
