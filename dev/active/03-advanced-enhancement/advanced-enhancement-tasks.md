# 03: Advanced Enhancement — Tasks

## Stage 0: Test Prerequisites
- [ ] Run full test suite — confirm all green
- [ ] Write `test_clahe_improves_local_contrast` (red) — measure local variance of L channel patches
- [ ] Write `test_saturation_curve_boosts_midrange` (red) — mid-S pixels boosted more than high-S
- [ ] Write `test_saturation_preserves_range` (red) — no values outside [0, 255]
- [ ] Write `test_edge_sharpening_increases_detail` (red) — Laplacian variance increases
- [ ] Write `test_edge_sharpening_no_noise_amplification` (red) — flat region std dev stable
- [ ] Review existing tests: `test_enhancement_increases_contrast`, `test_enhancement_increases_saturation` — note which assertions may need updating

## Stage 1: CLAHE Contrast
- [ ] Replace `_enhance_contrast` body with CLAHE implementation
- [ ] Use `cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))`
- [ ] Apply to L channel of LAB image
- [ ] Remove or deprecate `self._contrast_factor` usage
- [ ] Verify `test_clahe_improves_local_contrast` passes (green)
- [ ] Update `test_enhancement_increases_contrast` if assertion logic no longer matches
- [ ] Verify `test_enhancement_preserves_dimensions` and `test_enhancement_returns_rgb` still pass

## Stage 2: Saturation Curve
- [ ] Replace `_enhance_saturation` body with curve: `S_new = S + boost * S * (1 - S/255)`
- [ ] Define `_SATURATION_BOOST = 0.4` as class constant
- [ ] Clip result to [0, 255]
- [ ] Remove or deprecate `self._saturation_factor` usage
- [ ] Verify `test_saturation_curve_boosts_midrange` passes (green)
- [ ] Verify `test_saturation_preserves_range` passes (green)
- [ ] Update `test_enhancement_increases_saturation` if assertion logic changed

## Stage 3: Edge-Aware Sharpening
- [ ] Add `_sharpen` method to `ImageEnhancer`
- [ ] Step 1: bilateral filter `cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)`
- [ ] Step 2: unsharp mask `sharpened = img + alpha * (img - bilateral_output)` with alpha=0.5
- [ ] Clip to [0, 255]
- [ ] Call `_sharpen` at end of `enhance()` (after contrast + saturation)
- [ ] Verify `test_edge_sharpening_increases_detail` passes (green)
- [ ] Verify `test_edge_sharpening_no_noise_amplification` passes (green)
- [ ] Run full test suite — all green

## Stage 4: Before/After Toggle
- [ ] In `_run_pipeline` (`routes.py`): save pre-enhancement crop as `pre_enhance.png` in mosaic's temp dir
- [ ] Add `GET /api/preview/{mosaic_id}/original` endpoint — returns pre-enhancement image
- [ ] Add toggle button to `static/index.html` in step 4: "Show Original / Show Enhanced"
- [ ] Update `static/js/app.js` to swap `previewImage.src` on toggle
- [ ] Write `test_before_after_endpoint` integration test
- [ ] Manual QA: verify toggle shows clear visual difference

## Stage 5: Config Cleanup
- [ ] Assess whether `CONTRAST_FACTOR` and `SATURATION_FACTOR` in `config.py` are still used
- [ ] If unused: remove them and update `ImageEnhancer.__init__` signature
- [ ] If other code references them: keep as deprecated or repurpose
- [ ] Update docstrings on `ImageEnhancer` to describe new behavior

## Final
- [ ] Run full test suite — all green
- [ ] Review: no debug prints, no hardcoded paths
- [ ] Commit with message: `feat: upgrade enhancement to CLAHE, saturation curve, edge-aware sharpening`
