# Change Settings Button — Plan

## Overview

Add a "Change Settings" button to the Preview step (step 4) that navigates back to the Process step (step 3), preserving all user-selected settings (mosaic mode, color depth, tile size).

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC1 | A "Change Settings" button is visible on the Preview step (step 4), alongside "Download PDF" and "Start Over" |
| AC2 | Clicking "Change Settings" navigates back to the Process step (step 3) |
| AC3 | Previously selected settings (color count, tile size, mosaic mode) are preserved when returning to step 3 |
| AC4 | The user can re-generate a mosaic from step 3, which naturally replaces the old one |
| AC5 | No backend changes required — the cropped image persists via `state.croppedImageId` |

## Non-Goals

- No backend API changes
- No cleanup/disposal of old mosaic data on "back" (natural replacement only)
- No new automated tests (purely presentational; existing `showStep` and process flow already covered)

## Traceability

| AC | Code Areas | Verification |
|----|-----------|--------------|
| AC1 | `static/index.html` — add button in `.actions` div | Visual inspection |
| AC2 | `static/js/app.js` — click handler calls `showStep(stepProcess)` | Manual test |
| AC3 | No code needed — DOM form elements retain values when hidden/shown | Manual test |
| AC4 | Already works — `processBtn` handler reads current form values + `state.croppedImageId` | Existing `/api/process` tests |
| AC5 | N/A | N/A |

## Stage 1: Add "Change Settings" Button

**Goal**: User can navigate from Preview back to Process step
**Success Criteria**: Button visible, click returns to step 3 with settings preserved
**Status**: Complete

### Changes

1. **`static/index.html`**: Add `<button id="change-settings-btn" class="btn btn-secondary">Change Settings</button>` in the `.actions` div, between "Download PDF" and "Start Over"

2. **`static/js/app.js`**:
   - Add DOM reference: `const changeSettingsBtn = document.getElementById('change-settings-btn');`
   - Add click handler: `changeSettingsBtn.addEventListener('click', () => showStep(stepProcess));`

3. **No CSS changes**: Existing `.btn-secondary` and `.actions` flex layout handle styling

### Edge Cases

- **Re-generation**: Each `/api/process` call creates a new `mosaic_id`; old mosaics evicted naturally from `_mosaic_store`
- **Settings preservation**: HTML form elements retain state when hidden/shown; no save/restore needed
- **`state.croppedImageId`**: Persists across step transitions; no reset needed
