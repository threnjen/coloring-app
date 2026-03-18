# Phase 2: Mosaic Modes & Color Refinement

**Status**: Not Started
**Dependencies**: Phase 1 (Core Pipeline POC)
**Cross-references**: [PHASES_OVERVIEW.md](PHASES_OVERVIEW.md) | [PHASE_1_CORE_PIPELINE.md](PHASE_1_CORE_PIPELINE.md)

---

## Goal

Extend the core pipeline with circle mosaic rendering, a component size selector (4mm/5mm/6mm), advanced image enhancement, and manual color palette editing with live preview updates. After this phase, the full mosaic rendering feature set is complete.

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC2.1 | User can choose between square (pixel) and circle mosaic modes |
| AC2.2 | Circle mode renders circles in a grid with black inter-cell space (not touching) |
| AC2.3 | User can select component size: 4mm, 5mm, or 6mm |
| AC2.4 | Grid dimensions adjust correctly per size (50×65 at 4mm, 40×52 at 5mm, 33×43 at 6mm) |
| AC2.5 | App applies advanced enhancement: adaptive contrast (CLAHE), saturation curves, edge-aware sharpening |
| AC2.6 | User can view the color palette and manually swap or adjust any color |
| AC2.7 | When a user edits a color, all affected grid cells update and the preview refreshes |
| AC2.8 | PDF output respects the selected mode (square or circle) and component size |
| AC2.9 | Circle mode PDF renders circles with labels centered inside each circle |
| AC2.10 | Legend page works correctly for both modes |

## Architecture Changes

### New/Modified Files

| File | Change |
|------|--------|
| `src/config.py` | Add grid dimension lookup table for all 3 sizes; add mosaic mode enum |
| `src/processing/enhancement.py` | Add CLAHE, saturation curve adjustment, edge-aware sharpening |
| `src/rendering/grid_square.py` | Renamed from `grid.py` — square-specific rendering |
| `src/rendering/grid_circle.py` | New — circle grid rendering with black inter-cell space |
| `src/rendering/preview.py` | Support both modes; accept mode parameter |
| `src/rendering/pdf.py` | Support both modes and all sizes; layout adjusts per grid dimensions |
| `src/api/routes.py` | Add `mode` and `size` parameters to `/api/process` |
| `src/api/schemas.py` | Add `MosaicMode` enum, `ComponentSize` enum |
| `static/js/app.js` | Add mode toggle (square/circle), size dropdown, color palette editor UI |
| `static/css/style.css` | Styles for mode toggle, size selector, palette editor |

### Circle Grid Rendering

- Each cell is a circle inscribed within the grid cell square
- Circle diameter = component size minus a fixed gap (e.g., 0.5mm black border)
- Background between circles is solid black
- Label character centered inside each circle
- At 4mm: circle diameter ~3.5mm with ~0.25mm gap on each side

### Color Palette Editor

- After processing, display the palette as a row/grid of color swatches
- Click a swatch to open a color picker (browser native `<input type="color">`)
- On color change: the backend re-maps affected cells and returns updated grid + preview
- Alternatively, frontend-only preview update (re-render the preview canvas with new color) and only regenerate PDF on demand

### Enhancement Pipeline (Advanced)

1. **CLAHE** (Contrast Limited Adaptive Histogram Equalization) — better local contrast than global enhancement
2. **Saturation curve** — boost mid-range saturation more than already-saturated areas; prevent clipping
3. **Edge-aware sharpening** — sharpen details without amplifying noise (bilateral filter + unsharp mask)
4. **User should ideally see before/after** — toggle to compare enhanced vs original crop

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Circle mode at 4mm with 20 colors | Labels must fit inside 3.5mm circle — verify font size is legible |
| Size change after processing | Re-run grid generation (not the full pipeline); quantized colors stay the same |
| Color edit to a color already in palette | Warn or merge: "This color is already used as label X" |
| Color edit resulting in two very similar colors | Warn if LAB distance < threshold: "Colors X and Y may be hard to distinguish" |
| Switching mode after editing colors | Preserve edited palette; only re-render grid |

## Test Plan

### Unit Tests

| Test | Maps to |
|------|---------|
| `test_circle_grid_dimensions_4mm` | AC2.4 — 50×65 grid |
| `test_circle_grid_dimensions_5mm` | AC2.4 — 40×52 grid |
| `test_circle_grid_dimensions_6mm` | AC2.4 — 33×43 grid |
| `test_circle_rendering_has_black_gaps` | AC2.2 — verify black pixels exist between circles |
| `test_clahe_improves_local_contrast` | AC2.5 — local variance increases |
| `test_saturation_boost_preserves_range` | AC2.5 — no channel clipping |
| `test_color_swap_updates_grid` | AC2.7 — after swap, all cells with old color now have new color |
| `test_pdf_circle_mode_renders_circles` | AC2.9 — PDF inspection shows circular drawing commands |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_pipeline_circle_mode` | Full pipeline with circle mode → verify PDF renders circles |
| `test_size_change_preserves_palette` | Process at 4mm → change to 6mm → palette remains identical |
| `test_color_edit_round_trip` | Process → edit color → download PDF → verify legend reflects edit |

### Top 5 High-Value Test Cases

1. **Given** a processed mosaic at 4mm square, **When** user switches to circle mode, **Then** preview updates to show circles with black gaps, same colors and labels.

2. **Given** a 4mm circle grid with 20 colors, **When** PDF generated, **Then** all labels are legible inside 3.5mm circles.

3. **Given** a processed mosaic, **When** user changes size from 4mm to 6mm, **Then** grid changes to 33×43, palette stays the same, and the preview image is recognizable as the same subject.

4. **Given** a processed mosaic with 15 colors, **When** user swaps color #5 from red to blue, **Then** all cells labeled "5" change to blue in preview, and the legend updates.

5. **Given** a low-contrast photo, **When** processed with CLAHE + saturation boost, **Then** the quantized colors are more distinct than Phase 1 basic enhancement (measured by mean pairwise LAB distance).

## QA Manual Test Scenarios

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| QA1 | Mode toggle | Process an image, switch between Square and Circle | Preview changes between pixel grid and circle grid |
| QA2 | Size selector | Process, then change 4mm → 5mm → 6mm | Grid density visibly changes; image still recognizable |
| QA3 | Circle PDF | Generate PDF in circle mode | Circles with labels, black background between them |
| QA4 | Color editing | Click a palette swatch, pick new color | Affected cells in preview update to new color |
| QA5 | Edit + download | Edit 2 colors, then download PDF | PDF reflects edited colors in both grid and legend |
| QA6 | Enhancement comparison | Toggle before/after enhancement view | Clear difference in contrast and color vibrancy |
| QA7 | Similar color warning | Edit a color to be nearly identical to another | Warning message appears |
