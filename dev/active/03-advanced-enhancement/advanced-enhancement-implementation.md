# Implementation Record: 03 Advanced Enhancement

## Summary

Upgraded `ImageEnhancer` to use CLAHE for adaptive contrast, a nonlinear saturation curve for diminishing-returns saturation boost, and edge-aware sharpening via bilateral filter + unsharp mask. Added a before/after toggle: processing saves the pre-enhancement crop alongside the mosaic preview, and a new `GET /api/preview/{mosaic_id}/original` endpoint serves it. The UI toggle swaps the preview between enhanced and original views.

---

## Acceptance Criteria Status

| AC | Description | Status | Implementing Files | Notes |
|----|-------------|--------|--------------------|-------|
| AC2.5 (CLAHE) | Adaptive contrast replaces global scaling | Done | `src/processing/enhancement.py` | `cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))` on LAB L-channel |
| AC2.5 (saturation) | Saturation curve with diminishing returns | Done | `src/processing/enhancement.py` | `S + 0.4·S·(1−S/255)` curve |
| AC2.5 (sharpening) | Edge-aware sharpening added | Done | `src/processing/enhancement.py` | Bilateral filter + unsharp mask with α=0.5 |
| AC2.5 (before/after) | Before/after toggle in UI | Done | `src/api/routes.py`, `static/index.html`, `static/js/app.js` | New `/original` endpoint + checkbox toggle |

---

## Files Changed

### Source Files

| File | Change Type | What Changed | Why |
|------|-------------|--------------|-----|
| `src/processing/enhancement.py` | Modified | Replaced global contrast scaling with CLAHE; replaced linear saturation multiplier with curve; added `_sharpen` method; removed constructor params and config imports | AC2.5: all three enhancement improvements |
| `src/config.py` | Modified | Removed `CONTRAST_FACTOR` and `SATURATION_FACTOR` constants | Now unused after enhancement refactor |
| `src/api/routes.py` | Modified | `_run_pipeline` saves pre-enhancement image and returns it; `process_image` saves `pre_enhance.png`; added `GET /preview/{mosaic_id}/original` endpoint | AC2.5: before/after toggle |
| `static/index.html` | Modified | Added checkbox toggle "Show original (pre-enhancement)" in Step 4 | AC2.5: UI toggle |
| `static/js/app.js` | Modified | Added `toggleOriginal` reference; wired change event to swap `previewImage.src`; reset toggle on restart | AC2.5: UI toggle logic |

### Test Files

| File | Change Type | What Changed | Covers |
|------|-------------|--------------|--------|
| `tests/test_enhancement.py` | Modified | Removed constructor params from existing tests; added 6 new tests: `test_clahe_improves_local_contrast`, `test_clahe_preserves_dimensions`, `test_saturation_curve_boosts_midrange`, `test_saturation_preserves_range`, `test_edge_sharpening_increases_detail`, `test_edge_sharpening_no_noise_amplification` | AC2.5 (all three sub-features) |
| `tests/test_integration.py` | Modified | Added `test_before_after_endpoint` | AC2.5 before/after endpoint |

---

## Test Results

- **Baseline**: 58 passed, 0 failed
- **Final**: 65 passed, 0 failed
- **New tests added**: 7
- **Regressions**: None

---

## Deviations from Plan

None. All stages implemented as specified.

---

## Gaps

None.

---

## Reviewer Focus Areas

- [`src/processing/enhancement.py`](../../../src/processing/enhancement.py) — all three new methods; verify CLAHE tile size and clip limit are reasonable for 4000px images, and that the sharpening alpha (0.5) does not cause halo artifacts on real photos
- [`src/api/routes.py`](../../../src/api/routes.py) — `_run_pipeline` now returns a 4-tuple; confirm the `pre_enhance.png` is saved at the correct dimensions (resized to match preview dimensions) and that the new `/original` endpoint is correctly registered before `/preview/{mosaic_id}` to avoid routing conflicts
- `test_saturation_curve_boosts_midrange` in [`tests/test_enhancement.py`](../../../tests/test_enhancement.py) — relies on specific RGB→HSV round-trip values (RGB(200,160,160) and RGB(200,74,74)); verify these produce the expected S values on the target platform
