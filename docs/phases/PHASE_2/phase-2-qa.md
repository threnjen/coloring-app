# QA Plan: Phase 2 — Mosaic Modes

**Date:** 2026-03-27
**Mode:** Release QA Plan
**Scope:** Four sub-features — Component Size Selector, Mosaic Modes, Advanced Enhancement, Color Palette Editor
**Environment:** Local dev (`uvicorn src.main:app --reload` at http://127.0.0.1:8000)
**Browsers:** Chrome, Safari
**Prerequisites:**
- Python 3.12+ with `.venv` activated and `pip install -r requirements.txt` complete
- Dev server running (`uvicorn src.main:app --reload`)
- At least two test images: one JPEG (photo with varied colors), one PNG (any subject). Tester's choice.

## References

- Plan + Implementation + Review: `01-component-size-selector/`
- Plan + Implementation + Review: `02-mosaic-modes/`
- Plan + Implementation + Review: `03-advanced-enhancement/`
- Plan + Implementation + Review: `04-color-palette-editor/`

---

## Summary of Changes

Phase 2 adds four features on top of the Phase 1 core pipeline:

1. **Component Size Selector** — Dropdown to choose 3mm/4mm/5mm component size; grid dimensions adjust accordingly.
2. **Mosaic Modes** — Radio toggle for Square/Circle/Hexagon; each mode renders differently in preview and PDF.
3. **Advanced Enhancement** — CLAHE contrast, saturation curve, edge-aware sharpening; before/after toggle.
4. **Color Palette Editor** — Click any palette swatch to open a color picker; preview refreshes live; warnings for similar/duplicate colors.

## Automated Test Coverage

The following behaviors are verified by the 81 automated tests and do **not** need manual QA:

- Grid dimension lookup table correctness for all size × mode combinations
- API validation: invalid size (rejected), invalid mode, invalid hex color, out-of-range color index, unknown mosaic ID → proper 4xx errors
- PDF structure: 2 pages, valid `%PDF-` header, legend contains all colors
- PDF layout math at 4mm and 5mm sizes
- Preview pixel-level checks: circle has black gaps, hexagon has black gaps and odd-row offset, pointy-top orientation
- Palette mutation: color swap updates RGB array, labels preserved, grid unchanged
- Warning logic: LAB distance < 15 triggers similarity warning, exact RGB match triggers duplicate warning
- Enhancement algorithms: CLAHE local contrast improvement, saturation curve mid-range boost, sharpening detail increase without noise amplification
- Before/after endpoint: returns image, 404 for unknown ID
- Full pipeline integration for circle and hexagon modes

---

## Manual QA Checklist

### 1. Component Size Selector

**Acceptance Criteria:** AC2.3, AC2.4, AC2.12

#### Happy Path

- [ ] **Select 3mm size and process** — Upload a photo, crop it, leave size at "3mm (60×80)" (default), click Generate Mosaic. **Expected:** Preview image appears showing a 60-column × 80-row grid of colored squares.
- [ ] **Select 4mm size and process** — Change the size dropdown to "4mm (50×65)", click Generate Mosaic. **Expected:** Preview image appears with visibly larger cells and fewer of them (50×65 grid). The mosaic looks coarser than the 3mm version.
- [ ] **Select 5mm size and process** — Change the size dropdown to "5mm (40×52)", click Generate Mosaic. **Expected:** Preview image appears with even larger cells and fewer of them (40×52 grid). The mosaic is the coarsest of the three.
- [ ] **Size dropdown labels update per mode** — Select Hexagon mode. **Expected:** The size dropdown labels change to show hexagon dimensions (e.g., "3mm (60×93)", "4mm (45×70)", "5mm (36×56)"). Switch back to Square mode. **Expected:** Labels revert to square dimensions.

#### PDF Verification

- [ ] **PDF at 4mm reflects component size** — Process at 4mm, click Download PDF. Open the PDF. **Expected:** Grid cells are visibly larger than a 3mm PDF; grid area fills the page with appropriate margins. Legend page present.
- [ ] **PDF at 5mm reflects component size** — Process at 5mm, click Download PDF. Open the PDF. **Expected:** Grid cells are largest; fewer cells visible. Grid area fills the page with appropriate margins. Legend page present.

---

### 2. Mosaic Modes

**Acceptance Criteria:** AC2.1, AC2.2, AC2.8, AC2.9, AC2.10, AC2.11, AC2.13

#### Happy Path — Circle Mode

- [ ] **Circle mode preview** — Select Circle mode, click Generate Mosaic. **Expected:** Preview shows colored circles arranged in a grid with black gaps between them (not touching). Circles are uniformly sized and aligned.
- [ ] **Circle mode PDF** — Click Download PDF. Open the PDF. **Expected:** Page 1 shows filled colored circles with centered number labels inside each circle. Black background visible between circles. Labels are legible.
- [ ] **Circle mode legend** — Check page 2 of the circle PDF. **Expected:** Legend shows all colors with their number labels, same as square mode. Legend is unaffected by mode choice.

#### Happy Path — Hexagon Mode

- [ ] **Hexagon mode preview** — Select Hexagon mode, click Generate Mosaic. **Expected:** Preview shows colored pointy-top hexagons in an offset grid (odd rows shifted right by half a cell). Black gaps visible between hexagons. Hexagons are uniformly sized.
- [ ] **Hexagon mode PDF** — Click Download PDF. Open the PDF. **Expected:** Page 1 shows filled colored pointy-top hexagons with centered number labels. Odd rows are offset. Black background between hexagons. Labels are legible.
- [ ] **Hexagon mode legend** — Check page 2 of the hexagon PDF. **Expected:** Legend present with all colors and labels, same format as other modes.

#### Visual Consistency

- [ ] **Square mode still works** — Select Square mode, process. **Expected:** Preview and PDF render as grid of square cells with number labels (same as Phase 1 behavior). No visual regressions.
- [ ] **Mode switch preserves quality** — Process the same image in all three modes at the same size. Compare the three previews. **Expected:** Colors are consistent across modes (same palette). Cell count matches expected grid dimensions. Each mode has its distinctive shape.

#### Edge Cases

- [ ] **Hexagon edge clipping** — In hexagon mode at 3mm, examine the right edge of the preview and PDF. **Expected:** Offset-row hexagons may extend slightly past the grid area — this is acceptable within the margin. No hexagons are cut off in a jarring way.
- [ ] **Hexagon label legibility at 3mm** — Process at 3mm hexagon mode with 20 colors. Open the PDF and inspect labels in the hexagons. **Expected:** Labels are present and printed inside each hexagon. Labels may be tight at this size — note any illegibility for future improvement but this is not a blocker.

---

### 3. Advanced Enhancement

**Acceptance Criteria:** AC2.5

#### Happy Path

- [ ] **Enhanced preview looks better than original** — Upload and process a photo (any mode/size). Check the "Show original (pre-enhancement)" toggle in Step 4. **Expected:** Toggling it swaps between the enhanced mosaic preview and the original (pre-enhancement) crop. The enhanced version should have noticeably better contrast and color vibrancy compared to the original.
- [ ] **Toggle is responsive** — Click the "Show original" checkbox on and off multiple times. **Expected:** Preview image swaps each time without delay. No broken images or stale cache.
- [ ] **Toggle resets on restart** — Click "Start Over", then process a new image. **Expected:** The "Show original" checkbox is unchecked by default; preview shows the enhanced version.

#### Edge Cases

- [ ] **Already high-contrast photo** — Use a photo with strong contrast (e.g., black and white stripes or a sunset). Process it. Toggle before/after. **Expected:** Enhancement is subtle but doesn't introduce visible artifacts (halos, banding, or color shifts).
- [ ] **Low-saturation photo** — Use a muted or gray-ish photo. Process it. Toggle before/after. **Expected:** The enhanced version shows a noticeable saturation boost. No clipped-looking neon colors.

---

### 4. Color Palette Editor

**Acceptance Criteria:** AC2.6, AC2.7

#### Happy Path

- [ ] **Palette swatches are clickable** — After processing, observe the palette swatches below the preview. **Expected:** Each swatch shows a colored square with a label character. Clicking a swatch opens the browser's native color picker.
- [ ] **Edit a color and preview updates** — Click a swatch, pick a distinctly different color (e.g., change red to blue). Wait ~1 second. **Expected:** The swatch background updates to the new color immediately. The preview image refreshes to show the new color in all cells that had the old color. Labels on affected cells remain the same.
- [ ] **Edit multiple colors** — Change 2–3 different swatches to new colors. **Expected:** Each change refreshes the preview. Previously edited colors persist. The palette correctly reflects all edits.
- [ ] **Warnings for similar colors** — Edit a color to be very close (but not identical) to another palette color (e.g., #FF0000 and #FF0505). **Expected:** A warning message appears near the palette: something like "Color X is very similar to Y — they may be hard to distinguish."
- [ ] **Warning for duplicate color** — Edit a color to exactly match another palette entry. **Expected:** A warning message appears indicating the color is already used as another label. The edit still proceeds (warning is informational only).
- [ ] **Warning clears** — After seeing a warning, edit the same swatch to a distinct color. **Expected:** The warning message disappears.

#### PDF Round-Trip

- [ ] **PDF reflects edited palette** — Edit one or more palette colors, then click Download PDF. Open the PDF. **Expected:** The grid page shows the edited colors in the cells. The legend page shows the updated colors with their original labels. No stale/old colors appear.

#### Edge Cases

- [ ] **Rapid color picking** — Open a color picker and drag through colors quickly (changing the selection rapidly). **Expected:** The app debounces the changes; the preview doesn't flash/flicker excessively. After settling on a color for ~1 second, the preview updates once.
- [ ] **Edit color then switch to original toggle** — Edit a palette color, then check "Show original (pre-enhancement)." **Expected:** The original (pre-enhancement) image is shown. Uncheck the toggle. **Expected:** The enhanced preview with the edited color is shown.

---

### 5. Cross-Feature Interactions

- [ ] **Size + Mode combination** — Process at 4mm Hexagon mode. **Expected:** Preview shows hexagons in a 45×70 grid. Cells are visibly larger than 3mm hexagons. PDF matches.
- [ ] **Size + Mode + Palette edit** — Process at 5mm Circle mode, then edit a palette color. **Expected:** Preview refreshes showing circles at 5mm size with the edited color applied.
- [ ] **Full workflow: upload → crop → configure → preview → edit palette → download** — Run through the complete flow: upload JPEG, crop, select 4mm + Circle + 15 colors, process, edit 2 palette colors, toggle before/after, download PDF. **Expected:** Each step works. PDF contains the final edited palette in circle mode at 4mm.
- [ ] **Start Over resets everything** — After completing a full workflow, click "Start Over." **Expected:** Returns to Step 1. Size resets to 3mm, mode resets to Square, color count resets to 12, toggle is unchecked. Previous mosaic data is not shown.

---

### 6. Cross-Browser

- [ ] **Chrome — full workflow** — Run the full workflow (upload → crop → process → edit palette → download) in Chrome. **Expected:** All steps work. Color picker is the Chrome native picker. Preview updates. PDF downloads.
- [ ] **Safari — full workflow** — Run the full workflow in Safari. **Expected:** All steps work. Color picker is the Safari native picker. Preview updates. PDF downloads. Note any CSS differences (e.g., mode radio button highlighting may differ due to `:has()` selector support).

---

### 7. Error Handling (UI)

- [ ] **Upload non-image file** — Try uploading a `.txt` or `.pdf` file. **Expected:** Error message appears ("Upload failed" or similar). App stays on Step 1.
- [ ] **Upload oversized image** — Try uploading an image larger than 20MB (if available). **Expected:** Error message appears. App stays on Step 1.
- [ ] **Network interruption during palette edit** — Edit a palette color, then before the request completes, disconnect the network (e.g., toggle Wi-Fi off briefly). **Expected:** The swatch reverts to its previous color. No broken UI state. Reconnect and try again — edit should work.

---

## Notes

- The automated tests cover 81 cases including all API validation, rendering pixel checks, and algorithm correctness. This manual QA focuses on visual quality, UI interaction flow, and cross-feature integration that automated tests cannot verify.
- Review flagged that square PDF renders outlines (coloring sheet style) while circle/hex PDF renders filled colored shapes — this is by design per the plan but may warrant future UX consideration.
- Review flagged that hexagon PDF vertical centering had a bug (wrong `cy` offset) that was fixed but has no targeted regression test — visually verify hexagon label centering in the PDF.
- Enhancement parameters (CLAHE clip limit, sharpening alpha) are hardcoded defaults — if any photos show halo artifacts or over-sharpening, note for parameter tuning.
