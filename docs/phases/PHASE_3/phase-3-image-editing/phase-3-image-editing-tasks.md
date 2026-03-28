# Phase 3: Image Editing Tools — Tasks

## Stage 0: Dependencies & Infrastructure
- [ ] Add `rembg>=2.0.50,<3.0` to `requirements.txt`
- [ ] Install in venv, verify `import rembg` works
- [ ] Add config constants to `src/config.py`: `CUTOUT_MASK_BLUR_RADIUS`, `CUTOUT_MORPH_KERNEL_SIZE`, `COMPOSITE_MIN_SCALE`, `COMPOSITE_MAX_SCALE`, `PRESET_BACKGROUNDS_DIR`
- [ ] Create `static/presets/` directory (empty, with `.gitkeep`)
- [ ] Add `rembg` model download note to `README.md` setup section
- [ ] Verify existing tests still pass after dependency addition

## Stage 1: Backend — Cutout Processing
- [ ] Write `tests/test_cutout.py` with failing tests: `test_cutout_produces_rgba`, `test_cutout_returns_mask`, `test_cutout_mask_is_smooth`, `test_cutout_mask_feathered`
- [ ] Create `src/processing/cutout.py` with `CutoutProcessor` class
- [ ] Implement `remove_background()` — call `rembg.remove()`, extract alpha, clean mask, return (RGBA, mask)
- [ ] Implement `_clean_mask()` — morphological close/open + Gaussian blur
- [ ] Run tests — all pass
- [ ] Run full test suite — no regressions

## Stage 2: Backend — Background Provider
- [ ] Write `tests/test_backgrounds.py` with failing tests: `test_programmatic_backgrounds_list`, `test_programmatic_solid_generates_correct_color`, `test_programmatic_gradient_has_color_range`, `test_background_dimensions_match_request`, `test_preset_file_backgrounds`, `test_preset_filename_validation`, `test_custom_bg_resized_to_fill`
- [ ] Create `src/processing/backgrounds.py` with `BackgroundInfo` dataclass and `BackgroundProvider` class
- [ ] Implement `list_backgrounds()` — combine programmatic registry + file scan
- [ ] Implement `_generate_solid()` — solid color at given dimensions
- [ ] Implement `_generate_gradient()` — linear gradient via `np.linspace()`
- [ ] Implement `get_background()` — dispatch to generator or file loader + resize
- [ ] Implement file-based preset loading with filename validation regex
- [ ] Run tests — all pass
- [ ] Run full test suite — no regressions

## Stage 3: Backend — Compositing
- [ ] Write `tests/test_compositing.py` with failing tests: `test_composite_subject_position`, `test_composite_subject_scale`, `test_composite_scale_bounds`, `test_composite_dimensions_match_background`, `test_composite_output_is_rgb`, `test_composite_subject_overflow_clipped`, `test_composite_zero_offset`
- [ ] Create `src/processing/compositing.py` with `Compositor` class
- [ ] Implement `composite()` — scale subject, alpha-paste onto background, return RGB
- [ ] Handle scale clamping, position clipping, overflow
- [ ] Run tests — all pass
- [ ] Run full test suite — no regressions

## Stage 4: Backend — API Endpoints
- [ ] Add schema models to `src/api/schemas.py`: `CutoutRequest`, `CutoutResponse`, `BackgroundInfoSchema`, `BackgroundListResponse`, `CompositeRequest`, `CompositeResponse`
- [ ] Write `tests/test_image_editing_integration.py` with failing tests: `test_cutout_endpoint`, `test_cutout_invalid_id`, `test_cutout_nonexistent_image`, `test_backgrounds_endpoint`, `test_composite_with_preset_bg`, `test_composite_with_custom_upload`, `test_composite_invalid_cutout_id`, `test_cutout_to_pdf_pipeline`, `test_skip_editing_pipeline`
- [ ] Implement `POST /api/cutout` in `src/api/routes.py`
- [ ] Implement `GET /api/backgrounds` in `src/api/routes.py`
- [ ] Implement `POST /api/composite` in `src/api/routes.py` (JSON for preset bg, multipart for custom upload)
- [ ] Implement `GET /api/cutout/{cutout_id}/image` in `src/api/routes.py`
- [ ] Run tests — all pass
- [ ] Run full test suite — no regressions (especially `test_skip_editing_pipeline` confirming Phase 1 flow intact)

## Stage 5: Frontend — Editor UI
- [ ] Add `<section id="step-edit">` to `static/index.html` between step-crop and step-process
- [ ] Add `<script src="js/editor.js">` to `static/index.html`
- [ ] Create `static/js/editor.js` with editor state machine
- [ ] Implement cutout button — call API, display RGBA with checkerboard CSS background
- [ ] Implement background picker — fetch list, render thumbnails, click to select
- [ ] Implement custom background upload — file input, validation, upload
- [ ] Implement drag-to-position — vanilla JS pointer events on canvas overlay
- [ ] Implement scale slider — range input (0.25–2.0, step 0.05)
- [ ] Implement "Apply Composite" — call API, show preview, store composite_image_id
- [ ] Implement "Undo Composite" — revert to cutout + picker state
- [ ] Implement "Undo Cutout" — revert to original crop, hide editor
- [ ] Implement "Skip" button — go directly to process step
- [ ] Implement "Continue" button — pass composite_image_id or cropped_image_id to process
- [ ] Modify `static/js/app.js` — route crop → editor → process; update restart to clear editor state
- [ ] Add editor styles to `static/css/style.css`
- [ ] Manual QA: run through QA1–QA8 scenarios
- [ ] Run full test suite — no regressions

## Final Validation
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] `test_skip_editing_pipeline` confirms Phase 1 flow unchanged
- [ ] `test_cutout_to_pdf_pipeline` confirms full editing flow works end-to-end
- [ ] Manual QA scenarios QA1–QA8 pass
- [ ] Ruff lint passes (no E, F, I, W violations)
- [ ] No new security warnings (uploads validated, IDs validated, no path traversal)
