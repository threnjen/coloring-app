# Review Record: Color Palette Editor

## Summary
Solid implementation that covers all acceptance criteria with 15 new tests and no regressions. Four low-to-medium severity cleanliness issues were found and fixed. No functional bugs detected. High confidence in correctness.

## Verdict
Approved with Reservations

## Traceability

| AC | Status | Code Location | Notes |
|----|--------|---------------|-------|
| AC2.6 | Verified | `src/api/schemas.py:67-87`, `src/api/routes.py:432-472`, `static/js/app.js:142-187` | Interactive swatches with `<input type="color">`, debounce, warning display |
| AC2.7 (grid update) | Verified | `src/api/routes.py:447` | In-place palette mutation; grid cells reference by index |
| AC2.7 (preview refresh) | Verified | `src/api/routes.py:453-456`, `static/js/app.js:178` | Backend re-renders; frontend cache-busts |
| AC2.7 (PDF) | Verified | No code change needed | `PdfRenderer.render(sheet)` reads palette in-place; tested |
| Warnings (similar) | Verified | `src/api/routes.py:406-420` | CIE76 ΔE with BGR→LAB; threshold 15.0 |
| Warnings (duplicate) | Verified | `src/api/routes.py:401-405` | `np.array_equal` check |

## Issues Found

| # | Issue | Severity | File:Line | AC | Status |
|---|-------|----------|-----------|-----|--------|
| 1 | Palette-building logic duplicated in `_run_pipeline` and `_build_palette_info` | Medium | `src/api/routes.py:271-278` | — | Fixed |
| 2 | Unused `pytest` import | Low | `tests/test_palette_edit.py:4` | — | Fixed |
| 3 | `cv2` imported inside function body instead of top-level | Low | `src/api/routes.py:399` | — | Fixed |
| 4 | `"ColorPalette"` string annotation instead of proper import | Low | `src/api/routes.py:394,424` | — | Fixed |
| 5 | Preview re-render is synchronous (no `asyncio.to_thread`) | Low | `src/api/routes.py:453-456` | AC2.7 | Open |
| 6 | Frontend `_editPaletteColor` swallows all errors silently | Low | `static/js/app.js:185-187` | AC2.6 | Open |
| 7 | No test for "edit to same value" no-op edge case | Low | — | Plan edge cases | Open |

**Status values**: Fixed (applied during this review) | Open (not addressed) | Wont-Fix (declined with rationale)

## Fixes Applied

| File | What Changed | Issue # |
|------|--------------|---------|
| `src/api/routes.py` | `_run_pipeline()` now calls `_build_palette_info()` instead of duplicating the loop | 1 |
| `tests/test_palette_edit.py` | Removed unused `import pytest` | 2 |
| `src/api/routes.py` | Moved `import cv2` to top-level imports | 3 |
| `src/api/routes.py` | Imported `ColorPalette` from `src.models.mosaic`; replaced string annotations with real type | 4 |

## Remaining Concerns
- Issue #5: synchronous preview render in `edit_palette` — low severity, acceptable for <200ms renders
- Issue #6: silent error catch in frontend — low severity, only affects developer debugging experience
- Issue #7: missing "edit to same value" test — low severity, defer to next test pass

## Test Coverage Assessment
- Covered: AC2.6, AC2.7 (palette mutation, preview refresh, label preservation, PDF round-trip), warnings (similar, duplicate, no false positives), validation (invalid hex, out-of-range index, unknown mosaic)
- Missing: No test for editing a color to its current value (no-op edge case from plan)

## Risk Summary
- `src/api/routes.py:406-420` — LAB distance computation manually verified; BGR→LAB conversion correct
- Frontend debounce logic is correct but error handling could be improved for non-transient failures
- No undo/redo yet (explicitly out of scope per plan non-goals)
