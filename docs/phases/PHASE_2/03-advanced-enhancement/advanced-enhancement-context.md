# 03: Advanced Enhancement — Context

## Key Files

| File | Role | Key Symbols |
|------|------|-------------|
| `src/processing/enhancement.py` | `ImageEnhancer` class with `enhance()`, `_enhance_contrast()`, `_enhance_saturation()` | Currently uses global contrast scaling + linear saturation multiply |
| `src/config.py` | `CONTRAST_FACTOR = 1.3`, `SATURATION_FACTOR = 1.3` | May become unused after CLAHE/curve replace these |
| `src/api/routes.py` | `_run_pipeline()` — calls `enhancer.enhance(img)` | May need to store pre-enhancement image for before/after |
| `static/js/app.js` | Preview display logic | Needs before/after toggle |
| `static/index.html` | Step 4 "Preview & Download" | Needs toggle button |
| `tests/test_enhancement.py` | 4 existing tests | Some assertions may need updating for new behavior |

## Current Enhancement Implementation

`ImageEnhancer._enhance_contrast`:
- Converts RGB → LAB
- Scales L channel: `mean + factor × (L - mean)`, clips to [0, 255]
- Converts back to RGB
- Uses `CONTRAST_FACTOR = 1.3`

`ImageEnhancer._enhance_saturation`:
- Converts RGB → HSV
- Multiplies S channel by `SATURATION_FACTOR`, clips to [0, 255]
- Converts back to RGB

Both are global operations — apply the same transformation uniformly.

## Key Decisions

1. **Drop-in replacement**: `enhance()` method signature stays the same: `(image: Image.Image) -> Image.Image`. Callers don't change.

2. **Constructor simplification**: The new CLAHE/curve approach uses fixed parameters (clip limit, tile grid, boost factor) as class constants. The constructor's `contrast_factor` and `saturation_factor` params can be removed or ignored.

3. **Existing test compatibility**: `test_enhancement_increases_contrast` measures L-channel std dev change. CLAHE should also increase this, so the test likely still passes. `test_enhancement_increases_saturation` measures mean S increase — the curve should also increase mean S. But assertions may need relaxing or adjusting.

4. **Before/after is additive, not breaking**: The pre-enhancement image is saved as a side effect in `_run_pipeline`. A new GET endpoint serves it. The existing preview endpoint is unchanged.

## OpenCV APIs Used

- `cv2.createCLAHE(clipLimit, tileGridSize)` → `.apply(l_channel)` on single-channel array
- `cv2.bilateralFilter(src, d, sigmaColor, sigmaSpace)` → filtered array
- `cv2.cvtColor` for color space conversions (already used)
- Standard numpy for saturation curve math

## Constraints

- Images are capped at 4000px max dimension (from upload resize)
- Bilateral filter at d=9 on 4000px image: ~1-2s is acceptable
- All processing is CPU-bound, run in `asyncio.to_thread`
