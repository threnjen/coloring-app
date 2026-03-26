# 04: Color Palette Editor — Tasks

**Prerequisite**: 02-mosaic-modes must be complete (mode-aware preview rendering).

## Stage 0: Test Prerequisites
- [ ] Write `test_color_swap_updates_palette` (red) — edit index, verify `colors_rgb` changed
- [ ] Write `test_color_swap_preserves_labels` (red) — labels unchanged after edit
- [ ] Write `test_color_swap_preserves_grid` (red) — grid cells unchanged after edit
- [ ] Write `test_similar_color_warning` (red) — LAB distance < 15 triggers warning
- [ ] Write `test_duplicate_color_warning` (red) — exact RGB match triggers warning
- [ ] Write `test_palette_edit_endpoint` integration (red)
- [ ] Write `test_palette_edit_invalid_index` integration (red)
- [ ] Write `test_color_edit_round_trip` integration (red) — edit → PDF → verify

## Stage 1: Palette Edit Endpoint
- [ ] Add `PaletteEditRequest` schema to `src/api/schemas.py`:
  - `mosaic_id: str`
  - `color_index: int` (ge=0)
  - `new_color: str` (regex validated hex)
- [ ] Add `PaletteEditResponse` schema:
  - `palette: list[dict]`
  - `warnings: list[str]`
- [ ] Add `POST /api/palette/edit` route to `src/api/routes.py`
- [ ] Validate `mosaic_id` (UUID hex format)
- [ ] Validate `color_index` in range of palette
- [ ] Parse hex → RGB tuple
- [ ] Verify `test_palette_edit_endpoint` passes (green)
- [ ] Verify `test_palette_edit_invalid_index` returns 400 (green)

## Stage 2: Palette Update + Preview Re-render
- [ ] Update `palette.colors_rgb[color_index]` with new RGB values
- [ ] Re-render preview: call `PreviewRenderer.render(sheet.grid, sheet.palette)` with sheet's mode
- [ ] Save updated preview to temp dir (overwrite)
- [ ] Return updated palette info in response
- [ ] Verify `test_color_swap_updates_palette` passes (green)
- [ ] Verify `test_color_swap_preserves_labels` passes (green)
- [ ] Verify `test_color_swap_preserves_grid` passes (green)

## Stage 3: Similar Color Warning (LAB Distance)
- [ ] Convert new color RGB → LAB
- [ ] Convert each other palette color → LAB
- [ ] Compute Euclidean distance for each pair
- [ ] If any distance < 15.0: add warning string to response
- [ ] Define `_MIN_LAB_DISTANCE = 15.0` as constant
- [ ] Verify `test_similar_color_warning` passes (green)

## Stage 4: Duplicate Color Warning
- [ ] Check if new RGB exactly matches any other palette entry
- [ ] If match: add "This color is already used as label {X}" to warnings
- [ ] Verify `test_duplicate_color_warning` passes (green)
- [ ] Verify `test_no_warning_for_distinct_color` passes (no false positives)

## Stage 5: Frontend — Interactive Palette
- [ ] Update swatch creation in `app.js` to include `<input type="color" value="${c.hex}">`
- [ ] Hide the input, trigger on swatch click
- [ ] On `change` event: POST to `/api/palette/edit` with mosaic_id, color_index, new hex
- [ ] On success: update swatch background color
- [ ] Refresh preview: set `previewImage.src = /api/preview/${mosaicId}?t=${Date.now()}`
- [ ] Display warnings (if any) in a small message area near palette
- [ ] Add debounce: 500ms idle before sending API request
- [ ] Style editable swatches with cursor pointer, subtle hover effect
- [ ] Manual QA: edit colors, verify preview updates

## Stage 6: PDF Round-Trip Verification
- [ ] Verify `PdfRenderer.render(sheet)` reads current palette (should work automatically)
- [ ] Verify `test_color_edit_round_trip` passes (green) — edit → PDF → legend has new hex
- [ ] Manual QA: edit a color, download PDF, verify grid + legend show updated color

## Final
- [ ] Run full test suite — all green
- [ ] Review: no console.log, no debug code
- [ ] Commit with message: `feat: add interactive color palette editor with live preview`
