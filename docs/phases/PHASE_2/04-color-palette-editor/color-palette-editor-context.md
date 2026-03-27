# 04: Color Palette Editor — Context

## Key Files

| File | Role | Key Symbols |
|------|------|-------------|
| `src/models/mosaic.py` | `ColorPalette` — `colors_rgb: np.ndarray`, `label()`, `hex_color()` | `colors_rgb` is mutable ndarray — can update in place |
| `src/models/mosaic.py` | `MosaicSheet` — holds `palette`, `grid`, `mosaic_id` | Stored in `_mosaic_store` dict in routes |
| `src/api/routes.py` | `_mosaic_store: OrderedDict[str, MosaicSheet]` | In-memory store; palette edit reads/writes here |
| `src/api/routes.py` | `_run_pipeline()` — builds sheet, renders preview, saves to store | |
| `src/api/schemas.py` | `ProcessRequest`, `ProcessResponse` | Need new `PaletteEditRequest`, `PaletteEditResponse` |
| `src/rendering/preview.py` | `PreviewRenderer.render(grid, palette)` | Re-called after palette edit to refresh preview |
| `src/rendering/pdf.py` | `PdfRenderer.render(sheet)` | Reads `sheet.palette` — automatically uses edited palette |
| `static/js/app.js` | Palette display loop: creates `.palette-swatch` divs | Need to make interactive with `<input type="color">` |
| `static/index.html` | Step 4 preview section with `#palette-display` container | |

## Current Palette Display Code (app.js)

The process response handler builds read-only swatches:
```
for (const c of data.palette) {
    const swatch = document.createElement('div');
    swatch.className = 'palette-swatch';
    swatch.innerHTML = `
        <span class="swatch" style="background:${c.hex}"></span>
        <span>${c.label}</span>
    `;
    paletteDisplay.appendChild(swatch);
}
```

This needs to become interactive:
- Add hidden `<input type="color">` per swatch
- Click swatch → open picker
- On change → POST to `/api/palette/edit`

## Key Decisions

1. **In-place palette mutation**: `ColorPalette.colors_rgb` is a numpy array. Updating `colors_rgb[i] = [r, g, b]` mutates the existing palette object, which is shared by the `MosaicSheet` in `_mosaic_store`. No need to rebuild the sheet.

2. **Grid cells are NOT updated**: `GridCell.color_index` stays the same. The cell referencing `color_index=3` still references index 3 — the color *at* index 3 is what changes. Labels also stay the same.

3. **Preview overwrite strategy**: The re-rendered preview overwrites the same temp file. The existing `GET /api/preview/{mosaic_id}` endpoint serves from disk. To avoid browser caching stale previews, the frontend appends a cache-bust query param (e.g., `?t=Date.now()`).

4. **No frontend-only preview**: The Phase 2 spec mentioned an option for frontend-only preview re-rendering. This plan uses backend re-rendering for simplicity — the preview image is regenerated server-side and the frontend just fetches it. This works correctly for all modes (square, circle, hexagon) without duplicating rendering logic in JavaScript.

5. **Hex color validation**: The API validates the hex color string with a regex pattern `^#[0-9A-Fa-f]{6}$`. This catches malformed input before any processing.

## LAB Distance Reference

CIE76 ΔE (Euclidean distance in LAB space):
- ΔE < 1: not perceptible
- ΔE 1–2: perceptible on close inspection
- ΔE 2–10: perceptible at a glance
- ΔE 11–49: colors are more similar than different
- ΔE 50–100: colors are distinctly different

Threshold for "hard to distinguish" warning: ΔE < 15 (conservative; covers cases where colors look similar in small mosaic cells)

## Constraints

- Maximum 20 colors in palette (`MAX_COLORS = 20`)
- Labels are fixed by index: `0-9`, `A-J`
- Preview re-render should be fast (<200ms for 60×80 grid at 12px cells)
- `_mosaic_store` max size is 100 — editing doesn't change this limit
