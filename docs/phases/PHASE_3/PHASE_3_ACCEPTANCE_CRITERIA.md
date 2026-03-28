# Phase 3: Acceptance Criteria — Image Editing Tools

**Status**: Complete
**Phase Spec**: [PHASE_3_IMAGE_EDITING.md](PHASE_3_IMAGE_EDITING.md)
**Implementation Record**: [phase-3-image-editing-implementation.md](phase-3-image-editing/phase-3-image-editing-implementation.md)

---

## AC Summary

| ID | Criterion | Status | Verification |
|----|-----------|--------|-------------|
| AC3.1 | Cutout tool removes background | Done | Unit tests + integration tests |
| AC3.2 | Clean subject mask with smooth edges | Done | Unit tests |
| AC3.3 | Preset background library | Done | Unit tests + integration tests |
| AC3.4 | Custom background upload | Done | Unit tests + integration tests |
| AC3.5 | Position and scale subject | Done | Unit tests + integration tests |
| AC3.6 | Live composite preview | Done | Manual QA |
| AC3.7 | Pipeline compatibility | Done | Unit tests + integration tests |
| AC3.8a | Undo composite | Done | Manual QA |
| AC3.8b | Undo cutout | Done | Manual QA |
| AC3.9 | Works on common subjects | Partial | Documented gap — no real-photo integration test |

---

## AC3.1 — Cutout Tool Removes Background

**Criterion**: User can activate a cutout tool that removes the background from the cropped image.

**Implementation**:
- `src/processing/cutout.py` — `CutoutProcessor.remove_background()` wraps `rembg` (U2-Net model) to produce an RGBA image with an alpha mask separating subject from background.
- `src/api/routes.py` — `POST /api/cutout` accepts an `image_id`, runs background removal via `asyncio.to_thread()`, saves the RGBA result, and returns a `cutout_image_id`.
- `src/api/routes.py` — `GET /api/cutout/{cutout_id}/image` serves the cutout PNG for frontend display.

**Tests**:
- `tests/test_cutout.py::test_cutout_produces_rgba` — output has 4 channels with non-trivial alpha
- `tests/test_cutout.py::test_cutout_returns_mask` — separate grayscale mask returned, same dimensions as input
- `tests/test_image_editing_integration.py::test_cutout_endpoint` — endpoint returns 200 with valid cutout_image_id
- `tests/test_image_editing_integration.py::test_cutout_invalid_id` — rejects malformed IDs
- `tests/test_image_editing_integration.py::test_cutout_nonexistent_image` — returns 404 for missing images
- `tests/test_image_editing_integration.py::test_cutout_image_invalid_id` — cutout image endpoint rejects invalid IDs
- `tests/test_image_editing_integration.py::test_cutout_image_nonexistent` — cutout image endpoint returns 404

---

## AC3.2 — Clean Subject Mask

**Criterion**: Background removal produces a clean subject mask with smooth edges (feathered, not jagged).

**Implementation**:
- `src/processing/cutout.py` — `CutoutProcessor._clean_mask()` applies morphological close then open (removes small holes and noise) followed by Gaussian blur for edge feathering.
- `src/config.py` — `CUTOUT_MASK_BLUR_RADIUS` and `CUTOUT_MORPH_KERNEL_SIZE` control feathering and cleanup parameters.

**Tests**:
- `tests/test_cutout.py::test_cutout_mask_is_smooth` — verifies low edge gradient variance (no jagged aliasing)
- `tests/test_cutout.py::test_cutout_mask_feathered` — confirms alpha values between 0 and 255 exist at edges (gradual transition, not hard binary)

---

## AC3.3 — Preset Background Library

**Criterion**: User can choose from a library of preset solid-color and simple gradient backgrounds.

**Implementation**:
- `src/processing/backgrounds.py` — `BackgroundProvider` serves 9 programmatic backgrounds (6 solids: white, light gray, sky blue, pale yellow, mint green, light pink; 3 gradients: blue-to-white, sunset, forest) plus any file-based presets found in `static/presets/`.
- `src/processing/backgrounds.py` — `BackgroundInfo` dataclass describes each background (id, name, type, colors).
- `src/api/routes.py` — `GET /api/backgrounds` returns the full list of available backgrounds.
- File-based presets scanned from `static/presets/` with strict filename regex (`^[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$`) for path traversal defense.

**Tests**:
- `tests/test_backgrounds.py::test_programmatic_backgrounds_list` — returns expected count and types
- `tests/test_backgrounds.py::test_programmatic_solid_generates_correct_color` — white background pixels are (255, 255, 255)
- `tests/test_backgrounds.py::test_programmatic_gradient_has_color_range` — top and bottom rows differ
- `tests/test_backgrounds.py::test_background_dimensions_match_request` — output matches requested dimensions
- `tests/test_backgrounds.py::test_preset_file_backgrounds` — file-based presets discovered from directory
- `tests/test_backgrounds.py::test_preset_filename_validation` — rejects files with invalid names
- `tests/test_image_editing_integration.py::test_backgrounds_endpoint` — endpoint returns background list

---

## AC3.4 — Custom Background Upload

**Criterion**: User can upload a custom image to use as background.

**Implementation**:
- `src/api/routes.py` — `POST /api/composite` accepts multipart form data with a custom background file upload. The uploaded image passes through the same validation as photo uploads (magic bytes, size limit, format check).
- `src/processing/backgrounds.py` — `resize_to_fill()` scales small backgrounds up and center-crops large backgrounds to match composite dimensions.

**Tests**:
- `tests/test_backgrounds.py::test_custom_bg_resized_to_fill` — small backgrounds scaled up, large backgrounds center-cropped
- `tests/test_image_editing_integration.py::test_composite_with_custom_upload` — full round-trip: cutout → custom background upload → composite

---

## AC3.5 — Position and Scale Subject

**Criterion**: User can position and scale the cutout subject on the chosen background.

**Implementation**:
- `src/processing/compositing.py` — `Compositor.composite()` accepts `x`, `y` pixel offsets and a `scale` factor (clamped to 0.25–2.0 via `COMPOSITE_MIN_SCALE` / `COMPOSITE_MAX_SCALE` from config). Subject is resized with LANCZOS interpolation and alpha-composited onto the background at the specified position.
- `src/api/routes.py` — `POST /api/composite` accepts position and scale parameters via JSON body (preset backgrounds) or multipart form fields (custom uploads). Form value parsing is guarded with try/except for type conversion errors.

**Tests**:
- `tests/test_compositing.py::test_composite_subject_position` — subject placed at specified (x, y) offset
- `tests/test_compositing.py::test_composite_subject_scale` — subject dimensions match scale factor
- `tests/test_compositing.py::test_composite_scale_bounds` — scale outside 0.25–2.0 is clamped
- `tests/test_compositing.py::test_composite_subject_overflow_clipped` — subject extending beyond canvas is clipped without error
- `tests/test_compositing.py::test_composite_zero_offset` — subject at (0, 0) renders in top-left
- `tests/test_image_editing_integration.py::test_composite_with_preset_bg` — end-to-end composite with position and scale

---

## AC3.6 — Live Composite Preview

**Criterion**: User can see a live composite preview before proceeding to quantization.

**Implementation**:
- `static/js/editor.js` — `EditorManager` class implements a state machine (idle → cutout → cut → composited) with real-time preview. After cutout, the RGBA subject is displayed with a CSS checkerboard transparency pattern. Background picker thumbnails update the preview on click. Drag-to-position (pointer events) and scale slider update the preview transform in real-time via `_updatePreviewTransform()`.
- `static/index.html` — `<section id="step-edit">` added between crop and process steps with the editor UI (cutout button, background grid, scale slider, action buttons).

**Verification**: Manual QA scenarios QA1–QA6. Not automatable — visual rendering and interaction feedback require human verification.

---

## AC3.7 — Pipeline Compatibility

**Criterion**: The composite image feeds into the existing enhancement → quantization → grid pipeline unchanged.

**Implementation**:
- `src/processing/compositing.py` — `Compositor.composite()` returns an RGB image (no alpha channel) with the same dimensions as the background, ensuring compatibility with the downstream pipeline.
- `static/js/app.js` — After editor, the `composite_image_id` (or `cropped_image_id` if editing was skipped) is passed to the process step.

**Tests**:
- `tests/test_compositing.py::test_composite_dimensions_match_background` — output same size as background
- `tests/test_compositing.py::test_composite_output_is_rgb` — no alpha channel in final output
- `tests/test_image_editing_integration.py::test_cutout_to_pdf_pipeline` — full flow from cutout through PDF generation
- `tests/test_image_editing_integration.py::test_skip_editing_pipeline` — upload → crop → process works without editing (Phase 1 behavior preserved)

---

## AC3.8a — Undo Composite

**Criterion**: User can undo compositing and revert to the cutout + background picker state.

**Implementation**:
- `static/js/editor.js` — `_undoComposite()` clears the composite state and transitions back to the `cut` state, restoring the cutout preview with background picker and position controls.

**Verification**: Manual QA scenario QA6. State transitions verified during review (see review record, issue #2 fixed duplicate event listeners, issue #11 noted as low-severity wont-fix).

---

## AC3.8b — Undo Cutout

**Criterion**: User can undo cutout entirely and revert to the original cropped image.

**Implementation**:
- `static/js/editor.js` — `_undoCutout()` resets all editor state back to `idle`, hiding the editor panel and restoring the original crop view.

**Verification**: Manual QA scenario QA7. State transitions verified during review.

---

## AC3.9 — Works on Common Subjects

**Criterion**: Cutout tool works on common subjects: people, pets, objects against varied backgrounds.

**Implementation**:
- `src/processing/cutout.py` — Uses `rembg` with U2-Net model, which handles people, pets, and objects. Model runs locally (no external API).

**Verification**: Partial. Integration tests use a mocked `rembg` for speed and CI compatibility. No real-photo integration test exists — this would require large fixture files and real model inference. Documented as a known gap. Real-subject quality relies on manual QA scenarios QA1 (person, pet, object, ambiguous subject).

---

## Test Summary

| Metric | Value |
|--------|-------|
| Tests before Phase 3 | 100 |
| Tests after Phase 3 | 130 |
| New tests added | 30 (28 initial + 2 from review) |
| Regressions | 0 |
| All passing | Yes |

---

## Known Gaps

- **AC3.9 real-photo test**: No automated test with real photos — would require large fixtures and real `rembg` inference. Subject quality depends on manual QA.
- **QA1–QA8**: Frontend manual QA scenarios are not automatable. Visual rendering, drag interaction, and state transitions require human verification.
- **`_doComposite` error path**: On API error during compositing, state remains at `cut` implicitly rather than via explicit reset. Low severity — UI behaves correctly (review issue #11, wont-fix).
