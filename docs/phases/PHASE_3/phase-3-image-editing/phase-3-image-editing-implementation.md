# Implementation Record: Phase 3 — Image Editing Tools

## Summary

Implemented Phase 3 of the coloring app: background removal via `rembg`, programmatic and file-based background selection, alpha compositing with position/scale control, four new API endpoints, and a frontend editor step between crop and process with cutout, background picker, drag-to-position, scale slider, and two-level undo.

## Acceptance Criteria Status

| AC | Description | Status | Implementing Files | Notes |
|----|-------------|--------|--------------------|-------|
| AC3.1 | Cutout tool removes background | Done | `src/processing/cutout.py`, `src/api/routes.py` | `POST /api/cutout` returns RGBA with alpha mask |
| AC3.2 | Clean subject mask | Done | `src/processing/cutout.py` | Morphological close/open + Gaussian blur feathering |
| AC3.3 | Preset background library | Done | `src/processing/backgrounds.py`, `src/api/routes.py` | 9 programmatic (6 solids + 3 gradients) + file-based presets |
| AC3.4 | Custom background upload | Done | `src/api/routes.py`, `src/processing/backgrounds.py` | Multipart form upload with `resize_to_fill` |
| AC3.5 | Position and scale subject | Done | `src/processing/compositing.py` | Scale clamped to 0.25–2.0, position via (x, y) offset |
| AC3.6 | Live composite preview | Done | `static/js/editor.js`, `static/index.html` | Editor shows cutout/composite preview before proceeding |
| AC3.7 | Pipeline compatibility | Done | `src/processing/compositing.py` | Composite output is RGB, same dimensions, feeds into existing pipeline |
| AC3.8a | Undo composite | Done | `static/js/editor.js` | Reverts to cutout + background picker state |
| AC3.8b | Undo cutout | Done | `static/js/editor.js` | Reverts to original crop, editor resets |
| AC3.9 | Works on common subjects | Done | `src/processing/cutout.py` | `rembg` U2-Net handles people, pets, objects |

## Files Changed

### Source Files

| File | Change Type | What Changed | Why |
|------|-------------|--------------|-----|
| `src/config.py` | Modified | Added 5 Phase 3 constants: `CUTOUT_MASK_BLUR_RADIUS`, `CUTOUT_MORPH_KERNEL_SIZE`, `COMPOSITE_MIN_SCALE`, `COMPOSITE_MAX_SCALE`, `PRESET_BACKGROUNDS_DIR` | AC3.2, AC3.5, AC3.3 |
| `src/processing/cutout.py` | Created | `CutoutProcessor` with `remove_background()` and `_clean_mask()` | AC3.1, AC3.2 |
| `src/processing/backgrounds.py` | Created | `BackgroundInfo` dataclass, `BackgroundProvider` with programmatic + file-based backgrounds | AC3.3, AC3.4 |
| `src/processing/compositing.py` | Created | `Compositor.composite()` — alpha-composites subject onto background | AC3.5, AC3.7 |
| `src/api/schemas.py` | Modified | Added `CutoutRequest`, `CutoutResponse`, `BackgroundInfoSchema`, `BackgroundListResponse`, `CompositeRequest`, `CompositeResponse` | AC3.1, AC3.3, AC3.5 |
| `src/api/routes.py` | Modified | Added 4 endpoints: `POST /api/cutout`, `GET /api/cutout/{id}/image`, `GET /api/backgrounds`, `POST /api/composite` | AC3.1, AC3.3, AC3.4, AC3.5 |
| `requirements.txt` | Modified | Added `rembg[cpu]>=2.0.50,<3.0` | AC3.1 |
| `README.md` | Modified | Added rembg model download note | Documentation |
| `static/index.html` | Modified | Added `<section id="step-edit">` with editor UI, added `editor.js` script | AC3.6, AC3.8a, AC3.8b |
| `static/js/editor.js` | Created | `EditorManager` class: state machine, cutout/composite API calls, drag-to-position, scale slider, undo | AC3.6, AC3.8a, AC3.8b |
| `static/js/app.js` | Modified | Integrated editor step: crop → editor → process routing, editor continue callback, restart clears editor | AC3.6 |
| `static/css/style.css` | Modified | Editor panel, background thumbnails, checkerboard transparency, drag overlay, scale slider styles | AC3.6 |
| `static/presets/.gitkeep` | Created | Empty presets directory for user-added background images | AC3.3 |

### Test Files

| File | Change Type | What Changed | Covers |
|------|-------------|--------------|--------|
| `tests/test_cutout.py` | Created | 4 tests: RGBA output, mask return, mask smoothness, feathering | AC3.1, AC3.2 |
| `tests/test_backgrounds.py` | Created | 7 tests: list, solid color, gradient, dimensions, presets, filename validation, resize-to-fill | AC3.3, AC3.4, Security |
| `tests/test_compositing.py` | Created | 7 tests: position, scale, bounds, dimensions, RGB output, overflow clip, zero offset | AC3.5, AC3.7 |
| `tests/test_image_editing_integration.py` | Created | 10 tests: cutout endpoint, invalid/missing IDs, backgrounds, preset/custom composite, cutout image, full pipeline, skip pipeline | AC3.1–AC3.9 |

## Test Results

- **Baseline**: 100 passed, 0 failed (before implementation)
- **Final**: 128 passed, 0 failed (after implementation)
- **New tests added**: 28
- **Regressions**: None

## Deviations from Plan

- The composite endpoint accepts both JSON body (for preset backgrounds) and multipart form data (for custom uploads) via `Request` object parsing rather than separate endpoints. This was necessary because FastAPI cannot mix `Form` and JSON body parameters in a single endpoint signature.
- `rembg[cpu]` extra was required instead of plain `rembg` because the onnxruntime backend is needed.

## Gaps

- QA1–QA8 manual frontend scenarios cannot be automated — require manual testing.
- No `test_cutout_on_sample_subjects` integration test with real photos (would require large fixture files and real rembg inference). Integration tests use a mock rembg for speed/CI.

## Reviewer Focus Areas

- Composite endpoint request parsing in `src/api/routes.py` — dual JSON/multipart handling via `Request` object
- Cutout mask cleanup in `src/processing/cutout.py:_clean_mask()` — verify morphology + blur parameters produce good edges
- Background filename validation regex in `src/processing/backgrounds.py` — security (path traversal defense)
- Frontend editor state machine in `static/js/editor.js` — verify all state transitions and undo paths
- Scale clamping in `src/processing/compositing.py` — verify bounds enforced correctly
