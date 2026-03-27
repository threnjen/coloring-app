# 04: Color Palette Editor — Plan

**Status**: Not Started
**Dependencies**: Phase 1 (complete); 02-mosaic-modes (mode-aware preview rendering)
**Blocked by**: 02-mosaic-modes
**Blocks**: Nothing

---

## Requirements & Traceability

### Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC2.6 | User can view the color palette and manually swap or adjust any color |
| AC2.7 | When a user edits a color, all affected grid cells update and the preview refreshes |

### Non-Goals

- No undo/redo for color edits (future feature)
- No drag-to-reorder palette entries
- No "add color" or "remove color" — only swap/adjust existing colors
- No auto-suggest replacement colors
- Warning messages (similar color, duplicate) are informational only — don't block the edit

### Traceability

| AC | Code Areas | Planned Tests |
|----|------------|---------------|
| AC2.6 | `static/js/app.js`, `static/index.html`, `static/css/style.css` | Manual QA (UI interaction) |
| AC2.7 (grid update) | `src/api/routes.py`, `src/models/mosaic.py` | `test_color_swap_updates_palette`, `test_edited_palette_persists` |
| AC2.7 (preview refresh) | `src/rendering/preview.py`, `src/api/routes.py` | `test_palette_edit_returns_new_preview`, `test_preview_reflects_edited_color` |
| AC2.7 (PDF) | `src/rendering/pdf.py` | `test_pdf_uses_edited_palette` |
| Warnings | `src/api/routes.py` | `test_similar_color_warning`, `test_duplicate_color_warning` |

---

## Stage 0: Test Prerequisites

**Goal**: Write failing tests for palette editing behavior
**Success Criteria**: New tests red; existing tests green
**Status**: Not Started

## Stage 1: Palette Edit API Endpoint

**Goal**: New endpoint `POST /api/palette/edit` that accepts a color change and returns updated data
**Success Criteria**: Endpoint accepts mosaic_id + color_index + new hex color; returns updated palette + preview URL
**Status**: Not Started

### Design

Request schema (`PaletteEditRequest`):
- `mosaic_id: str`
- `color_index: int` (0-based, validated against palette size)
- `new_color: str` (hex string like "#FF00AA", validated with regex)

Response schema (`PaletteEditResponse`):
- `palette: list[dict]` (same format as `ProcessResponse.palette`)
- `warnings: list[str]` (empty list or warning messages)

### Endpoint Logic

1. Look up `MosaicSheet` from `_mosaic_store` by `mosaic_id`
2. Validate `color_index` is in range
3. Parse `new_color` hex → RGB tuple
4. Check for warnings (see Stage 3 and 4)
5. Update `palette.colors_rgb[color_index]` in-place
6. Re-render preview image
7. Return updated palette + warnings

## Stage 2: Backend — Palette Update + Preview Re-render

**Goal**: Update the stored `ColorPalette` and regenerate the preview image
**Success Criteria**: After edit, the mosaic sheet's palette reflects the new color; preview endpoint serves updated image
**Status**: Not Started

### Design

- `ColorPalette.colors_rgb` is a numpy array — update with `palette.colors_rgb[index] = [r, g, b]`
- Grid cells don't change — they reference `color_index`, and the palette at that index now has a new color. Labels stay the same.
- Re-render preview: call `PreviewRenderer.render(sheet.grid, sheet.palette)` with mode from sheet
- Save updated preview to temp dir (overwrite existing preview image)
- The existing `GET /api/preview/{mosaic_id}` endpoint serves the preview from disk — it will automatically serve the updated version

### Correctness

- Grid cells are NOT modified — only the palette array changes
- Labels remain the same (label "5" still means "5", it just maps to a different color)
- `hex_color()` method on `ColorPalette` naturally returns the updated hex

## Stage 3: LAB Distance Warning

**Goal**: Warn if the edited color is too similar to another palette entry
**Success Criteria**: If LAB distance between new color and any other palette color < threshold, warning returned
**Status**: Not Started

### Design

- Convert new RGB → LAB using `cv2.cvtColor`
- For each other palette color, compute Euclidean distance in LAB space
- If any distance < threshold (e.g., 15.0 in LAB units — roughly "hard to distinguish"), add warning: `"Color {label_new} is very similar to {label_existing} — they may be hard to distinguish"`
- Threshold as constant in config or class-level

## Stage 4: Duplicate Color Warning

**Goal**: Warn if the new color exactly matches another palette entry
**Success Criteria**: If new RGB == any other palette RGB, warning returned
**Status**: Not Started

### Design

- Simple array comparison: `np.array_equal(new_rgb, palette.colors_rgb[i])` for each `i != color_index`
- If match: `"This color is already used as label {label}"`
- This is a superset of the similarity warning (distance = 0) but with a more specific message

## Stage 5: Frontend — Interactive Palette Editing

**Goal**: Make palette swatches clickable with a color picker; refresh preview on edit
**Success Criteria**: User clicks swatch → native color picker opens → on change, API called, preview updates
**Status**: Not Started

### Design

- Currently `app.js` creates read-only `.palette-swatch` divs after processing
- Change each swatch to include an `<input type="color">` element
- On `input` or `change` event: POST to `/api/palette/edit` with `mosaic_id`, `color_index`, `new_color`
- On response: update swatch background, refresh `previewImage.src` (append cache-bust query param)
- Display warnings (if any) in a toast/alert near the palette

### UI Details

- Color picker opens on swatch click (the `<input type="color">` can be hidden, triggered by label click)
- Show label character on each swatch
- Debounce rapid color picker changes (defer API call until picker closes or 500ms idle)

## Stage 6: PDF Uses Edited Palette

**Goal**: PDF download reflects any palette edits
**Success Criteria**: After editing colors, PDF download shows updated colors in grid and legend
**Status**: Not Started

### Design

- `PdfRenderer.render(sheet)` already reads `sheet.palette` — since the palette is modified in place, the next PDF render naturally uses the updated colors
- No code change expected — just needs a test to verify the round trip

---

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Edit color to same value | No-op; no warning; preview unchanged |
| Edit color to value matching another | Duplicate warning returned; edit proceeds |
| Edit multiple colors rapidly | Debounce in frontend; each API call is atomic |
| Edit color then download PDF | PDF uses current palette state (edited) |
| Edit color then switch mode (from 02) | Palette preserved; mode change re-renders with edited palette |
| Invalid hex color string | API returns 400/422 validation error |
| Color index out of range | API returns 400 with descriptive error |
| Mosaic ID not found | API returns 404 |

## Clean Design Checklist

- [ ] Grid cells never modified during palette edit — only `colors_rgb` array changes
- [ ] No new model classes — reuse `ColorPalette`, `MosaicSheet`
- [ ] Warning logic is simple comparisons, not over-abstracted
- [ ] Debounce is frontend-only — backend handles each request independently
- [ ] Hex color validation uses regex, not try/except parsing

## Test Plan

### Unit Tests

| Test | AC |
|------|----|
| `test_color_swap_updates_palette` | AC2.7 — `palette.colors_rgb[i]` changes |
| `test_color_swap_preserves_labels` | AC2.7 — labels unchanged after edit |
| `test_color_swap_preserves_grid` | AC2.7 — grid cells unchanged after edit |
| `test_similar_color_warning` | AC2.6 — LAB distance < threshold triggers warning |
| `test_duplicate_color_warning` | AC2.6 — exact match triggers specific warning |
| `test_no_warning_for_distinct_color` | AC2.6 — distant color produces no warnings |
| `test_hex_color_validation` | AC2.6 — invalid hex rejected |

### Integration Tests

| Test | Description |
|------|----|
| `test_palette_edit_endpoint` | POST edit → 200 response with updated palette |
| `test_palette_edit_invalid_index` | POST edit with index=99 → 400 error |
| `test_palette_edit_preview_changes` | POST edit → fetch preview → pixels differ from before |
| `test_color_edit_round_trip` | Process → edit color → download PDF → verify legend has new color |

### Top 3 Given/When/Then

1. **Given** a processed mosaic with 12 colors, **When** user changes color at index 3 from red to blue via `POST /api/palette/edit`, **Then** the response palette shows the new blue at index 3, labels are unchanged, and the preview image has updated pixels.
2. **Given** a palette where color 5 is `#FF0000`, **When** user edits color 8 to `#FF0500` (LAB distance < 15), **Then** response includes a warning about colors 5 and 8 being hard to distinguish.
3. **Given** an edited palette, **When** PDF downloaded, **Then** the grid page uses the new colors and the legend page shows the edited hex values.
