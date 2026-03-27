# Review Record: Mosaic Modes

## Summary
Implementation matches planning docs across all 7 acceptance criteria. One correctness bug found (hexagon PDF vertical centering), one weak test, and two lint issues. All four were fixed during the review.

## Verdict
Approved with Reservations

## Traceability

| AC | Status | Code Location | Notes |
|----|--------|---------------|-------|
| AC2.1 | Verified | `src/api/schemas.py:12-18`, `src/models/mosaic.py:92`, `src/api/routes.py:236-273`, `static/index.html:51-67`, `static/js/app.js:115-131` | Enum, model, API, UI all wired |
| AC2.2 | Verified | `src/rendering/preview.py:118-140` | Black bg + ellipse with 1px gap |
| AC2.8 | Verified | `src/rendering/pdf.py:88-100` | Mode dispatch in `_draw_grid_page` |
| AC2.9 | Verified | `src/rendering/pdf.py:118-142` | `c.circle()` + centered `drawString` |
| AC2.10 | Verified | `src/rendering/pdf.py:175-232` | Legend is mode-independent |
| AC2.11 | Verified | `src/rendering/preview.py:142-170`, `src/rendering/geometry.py:1-23` | Pointy-top with odd-row offset |
| AC2.13 | Verified | `src/rendering/pdf.py:144-173` | Path ops correct; cy offset fixed |

## Issues Found

| # | Issue | Severity | File:Line | AC | Status |
|---|-------|----------|-----------|-----|--------|
| 1 | Hex PDF `cy` used `cell_pt/2` instead of `cell_pt*sqrt(3)/4` (row_spacing/2) | High | `src/rendering/pdf.py:155` | AC2.13 | Fixed |
| 2 | Palette preservation test only asserted `len()`, used different `cropped_id` | Medium | `tests/test_mosaic_modes_integration.py:92-110` | AC2.1 | Fixed |
| 3 | Square PDF draws outlines; circle/hex PDF draws filled shapes | Medium | `src/rendering/pdf.py:104-142` | AC2.8 | Wont-Fix |
| 4 | Unused import `PREVIEW_CELL_PX` + unsorted imports | Low | `tests/test_mosaic_modes.py:9` | — | Fixed |
| 5 | `getattr(sheet, "mode", "square")` defensive access unnecessary | Low | `src/rendering/pdf.py:57` | — | Fixed |
| 6 | Brightness calculation duplicated 3× in preview.py | Low | `src/rendering/preview.py:107,127,159` | — | Open |
| 7 | CSS `:has()` for mode-option styling | Low | `static/css/style.css:175` | — | Open |

**Status values**: Fixed (applied during this review) | Open (not addressed) | Wont-Fix (declined with rationale)

## Fixes Applied

| File | What Changed | Issue # |
|------|--------------|---------|
| `src/rendering/pdf.py` | Changed hex cell `cy = y + cell_pt / 2` → `cy = y + cell_pt * math.sqrt(3) / 4` | 1 |
| `src/rendering/pdf.py` | Changed `getattr(sheet, "mode", "square")` → `sheet.mode` | 5 |
| `tests/test_mosaic_modes.py` | Removed unused `PREVIEW_CELL_PX` import; combined `src.models.mosaic` imports to satisfy ruff isort | 4 |
| `tests/test_mosaic_modes_integration.py` | Reuse same `cropped_id` for both modes; assert palette hex values match | 2 |

## Remaining Concerns
- Issue #3: Square PDF renders outlines (coloring sheet); circle/hex PDF renders color-filled shapes. Intentional per plan but may confuse users expecting a blank sheet in all modes. Deferred to UX review.
- Issue #6: Brightness calculation duplicated 3× in `preview.py` — low severity, defer to next cleanup.
- Issue #7: CSS `:has()` selector — modern browser support only. Functional degradation is cosmetic only (no highlight on selected radio). Acceptable.

## Test Coverage Assessment
- Covered: AC2.1, AC2.2, AC2.8, AC2.9, AC2.10, AC2.11, AC2.13
- Missing: No test for hexagon PDF vertical positioning accuracy; no test for invalid mode API rejection
- Strengthened: Palette preservation test now uses same image and compares hex values

## Risk Summary
- `src/rendering/pdf.py:144-173` — hexagon PDF cy offset was wrong; fixed but no targeted regression test exists
- Circle/hex PDF fill behavior differs from square PDF outline behavior — potential user confusion
- Palette preservation depends on k-means determinism for same input → test may be fragile under different numpy/sklearn versions
