# Review Record: 03 Advanced Enhancement

## Summary
Implementation is clean, correct, and complete. All four AC2.5 sub-criteria (CLAHE, saturation curve, edge-aware sharpening, before/after toggle) are fully implemented and tested. No blockers found; four low-severity issues identified and fixed.

## Verdict
Approved

## Traceability

| AC | Status | Code Location | Notes |
|----|--------|---------------|-------|
| AC2.5 (CLAHE) | Verified | `src/processing/enhancement.py:43-52` | `createCLAHE(clipLimit=2.0, tileGridSize=(8,8))` on LAB L-channel |
| AC2.5 (saturation curve) | Verified | `src/processing/enhancement.py:54-59` | `S + 0.4*S*(1 - S/255)` curve with clip |
| AC2.5 (edge-aware sharpening) | Verified | `src/processing/enhancement.py:61-66` | Bilateral filter (d=9) + unsharp mask (alpha=0.5) |
| AC2.5 (before/after toggle) | Verified | `src/api/routes.py:354-362`, `static/index.html:83-88`, `static/js/app.js:178-183` | New endpoint + checkbox + src swap logic |

## Issues Found

| # | Issue | Severity | File:Line | AC | Status |
|---|-------|----------|-----------|-----|--------|
| 1 | No CSS for `.preview-toggle` container | Low | `static/css/style.css` | AC2.5 | Fixed |
| 2 | Stale QA.md references to removed config constants | Low | `docs/QA.md:58-59` | — | Fixed |
| 3 | Redundant `.astype(np.float32)` in `_sharpen` | Low | `src/processing/enhancement.py:64-65` | — | Fixed |
| 4 | No 404 test for `/preview/{id}/original` with bad ID | Low | `tests/test_integration.py` | AC2.5 | Fixed |
| 5 | `test_clahe_preserves_dimensions` duplicates `test_enhancement_preserves_dimensions` | Low | `tests/test_enhancement.py:80` | AC2.5 | Wont-Fix |

**Status values**: Fixed (applied during this review) | Open (not addressed) | Wont-Fix (declined with rationale)

## Fixes Applied

| File | What Changed | Issue # |
|------|--------------|---------|
| `static/css/style.css` | Added `.preview-toggle` CSS rule with margin | 1 |
| `docs/QA.md` | Removed `CONTRAST_FACTOR` and `SATURATION_FACTOR` rows | 2 |
| `src/processing/enhancement.py` | Cached `img.astype(np.float32)` in local variable in `_sharpen` | 3 |
| `tests/test_integration.py` | Added `test_original_preview_not_found` for 404 coverage | 4 |

## Remaining Concerns
- Issue #5: `test_clahe_preserves_dimensions` is a near-duplicate of `test_enhancement_preserves_dimensions` — low severity, both are cheap and label intent differently. No action needed.

## Test Coverage Assessment
- Covered: AC2.5 (CLAHE), AC2.5 (saturation curve), AC2.5 (sharpening), AC2.5 (before/after toggle)
- Added: 404 test for original preview endpoint
- No missing coverage against acceptance criteria

## Risk Summary
- Enhancement parameters (clip limit, tile grid, boost, alpha) are hardcoded class constants — reasonable defaults but may need tuning on real photos with halo artifacts at edges
- Color space round-trips (RGB→LAB→RGB→HSV→RGB) introduce minor quantization; standard and acceptable
- Bilateral filter is O(n) per pixel but images are capped at 4000px max dimension — acceptable latency
