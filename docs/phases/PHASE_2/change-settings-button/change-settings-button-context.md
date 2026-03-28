# Change Settings Button — Context

## Key Files

| File | Role |
|------|------|
| `static/index.html` | HTML structure — step sections, buttons, form controls |
| `static/js/app.js` | Step navigation (`showStep`), state management, event handlers |
| `static/css/style.css` | Styles for `.btn-secondary`, `.actions` flex layout |
| `src/api/routes.py` | Backend `/api/process` endpoint (no changes needed) |

## Architecture Notes

- **Step navigation**: `showStep(stepEl)` hides all steps and shows the target. Steps are `<section>` elements toggled via `hidden` attribute.
- **State object**: `state = { imageId, croppedImageId, mosaicId, originalFile }` — `croppedImageId` persists after crop step and is reused on re-processing.
- **Form state**: HTML `<input>`, `<select>`, and radio buttons retain their values when hidden/shown. No explicit state management needed.
- **Mosaic store**: Server-side `_mosaic_store` (OrderedDict, max 100) — old mosaics evicted FIFO. Re-generation creates a new entry.

## Decisions

| Decision | Rationale |
|----------|-----------|
| Frontend-only change | `state.croppedImageId` and DOM form state already persist; no backend support needed |
| No old mosaic cleanup on back | Natural replacement on re-generate is simpler; server eviction handles memory |
| `btn-secondary` styling | Matches "Start Over" button visual weight; "Change Settings" is a non-destructive action |
| Button placement between Download and Start Over | Logical flow: primary action (Download) → adjust (Change Settings) → reset (Start Over) |
