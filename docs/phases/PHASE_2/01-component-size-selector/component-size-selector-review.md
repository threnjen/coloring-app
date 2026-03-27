# Review Record: Component Size Selector

## Summary
Implementation is clean, well-scoped, and matches the plan with no deviations. One latent bug (wrong default on MosaicSheet), dead code, and minor test hygiene issues were found and fixed. Confident in correctness.

## Verdict
Approved with Reservations (all reservations resolved via fixes below)

## Traceability

| AC | Status | Code Location | Notes |
|----|--------|---------------|-------|
| AC2.3 | Verified | `src/api/schemas.py:41`, `static/index.html:47-54`, `static/js/app.js:24,124` | Dropdown + API field + Pydantic validation all correct |
| AC2.4 | Verified | `src/config.py:33-41`, `src/api/routes.py:248`, `src/rendering/pdf.py:55-58` | Lookup values match reference table; pipeline and PDF adapt dynamically |
| AC2.12 | Verified | `src/config.py:42-45` | Hexagon dimensions in lookup table match context doc exactly |

## Issues Found

| # | Issue | Severity | File:Line | AC | Status |
|---|-------|----------|-----------|-----|--------|
| 1 | `MosaicSheet.component_size_mm` defaulted to `4.0` instead of `3.0` | High | `src/models/mosaic.py:95` | AC2.3 | Fixed |
| 2 | Stale imports `COMPONENT_SIZE_MM`, `GRID_COLUMNS`, `GRID_ROWS` in routes.py | Medium | `src/api/routes.py:27-30` | — | Fixed |
| 3 | `test_pdf_different_color_counts` lost `%PDF-` header assertion | Medium | `tests/test_pdf.py:100` | — | Fixed |
| 4 | `ComponentSize` IntEnum defined but never used | Low | `src/config.py:22-27` | — | Fixed |
| 5 | `_make_sheet` helper duplicated sheet reconstruction in 4mm/5mm tests | Low | `tests/test_pdf.py:103-122` | — | Fixed |
| 6 | `PRINTABLE_WIDTH_MM`, `MARGIN_SIDE_MM` etc. are now 3mm-only legacy constants | Low | `src/config.py:54-59` | — | Open |

**Status values**: Fixed (applied during this review) | Open (not addressed) | Wont-Fix (declined with rationale)

## Fixes Applied

| File | What Changed | Issue # |
|------|--------------|---------|
| `src/models/mosaic.py` | Changed `component_size_mm` default from `4.0` to `3.0` | 1 |
| `src/api/routes.py` | Removed unused imports of `COMPONENT_SIZE_MM`, `GRID_COLUMNS`, `GRID_ROWS` | 2 |
| `tests/test_pdf.py` | Restored `assert pdf_bytes[:5] == b"%PDF-"` in `test_pdf_different_color_counts` | 3 |
| `src/config.py` | Removed unused `ComponentSize` IntEnum and `from enum import IntEnum` | 4 |
| `tests/test_pdf.py` | Added `component_size_mm` param to `_make_sheet()`, simplified 4mm/5mm tests | 5 |

## Remaining Concerns
- Issue #6: `PRINTABLE_WIDTH_MM`, `PRINTABLE_HEIGHT_MM`, `MARGIN_SIDE_MM`, `MARGIN_TOP_MM` in config.py describe 3mm-only values and are only used in one existing test. Low severity — defer cleanup to next pass or when they cause confusion.

## Test Coverage Assessment
- Covered: AC2.3 (default size, invalid size), AC2.4 (grid dimensions at 3/4/5mm, PDF layout at 4/5mm, lookup table), AC2.12 (hexagon lookup)
- Missing: No boundary test for `size=2` (only `size=7` tested for invalid). Pydantic handles it, but an explicit test would add confidence.

## Risk Summary
- Issue #1 was the only real bug — `MosaicSheet` default of 4.0 would silently produce wrong output for any future code path that omits `component_size_mm`. Now fixed.
- Stale imports and dead enum were hygiene issues, now removed.
- Implementation is well-aligned with the plan, lookup table is correct, and dynamic margin math is sound.
