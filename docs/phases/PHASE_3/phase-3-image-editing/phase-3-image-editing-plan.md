# Phase 3: Image Editing Tools — Plan

**Status**: Not Started
**Dependencies**: Phase 1 (Core Pipeline POC) — complete
**Spec**: `docs/phases/PHASE_3/PHASE_3_IMAGE_EDITING.md`

---

## Acceptance Criteria

| ID | Criterion | Testable Statement |
|----|-----------|--------------------|
| AC3.1 | Cutout tool removes background | `POST /api/cutout` accepts an image ID and returns an RGBA image with alpha mask |
| AC3.2 | Clean subject mask | Cutout mask edges are feathered (Gaussian blur) and morphologically cleaned — no jagged aliasing |
| AC3.3 | Preset background library | `GET /api/backgrounds` returns a list of available backgrounds (programmatic solids/gradients + file-based presets) |
| AC3.4 | Custom background upload | `POST /api/composite` accepts a custom uploaded image as background |
| AC3.5 | Position and scale subject | `POST /api/composite` accepts position (x, y) and scale (0.25–2.0); subject placed correctly |
| AC3.6 | Live composite preview | Frontend shows composite preview before proceeding to quantization |
| AC3.7 | Pipeline compatibility | Composite output is RGB, matches crop dimensions, feeds into existing enhance → quantize → grid pipeline unchanged |
| AC3.8a | Undo composite | User can undo compositing (revert to cutout + background picker state) |
| AC3.8b | Undo cutout | User can undo cutout entirely (revert to original cropped image, editor resets) |
| AC3.9 | Works on common subjects | Cutout works on people, pets, objects — verified by integration test |

## Non-Goals

- No manual mask editing / brush tool (fully automatic `rembg` only)
- No multiple subjects (one cutout per image)
- No animated/video backgrounds
- No server-side background library management UI (presets are static files or programmatic)
- No undo history beyond two levels (undo composite, undo cutout)

## Traceability Matrix

| AC | Code Areas | Planned Tests |
|----|------------|---------------|
| AC3.1 | `src/processing/cutout.py` → `CutoutProcessor.remove_background()` | `test_cutout_produces_rgba`, `test_cutout_returns_mask` |
| AC3.2 | `src/processing/cutout.py` → `CutoutProcessor._clean_mask()` | `test_cutout_mask_is_smooth`, `test_cutout_mask_feathered` |
| AC3.3 | `src/processing/backgrounds.py` → `BackgroundProvider`, routes → `GET /api/backgrounds` | `test_programmatic_backgrounds_list`, `test_preset_file_backgrounds`, `test_backgrounds_endpoint` |
| AC3.4 | `src/processing/compositing.py` → `Compositor.composite()`, routes → `POST /api/composite` | `test_composite_custom_background_upload`, `test_custom_bg_resized_to_fill` |
| AC3.5 | `src/processing/compositing.py` → `Compositor.composite()` | `test_composite_subject_position`, `test_composite_subject_scale`, `test_composite_scale_bounds` |
| AC3.6 | `static/js/editor.js` | Manual QA (QA1–QA8) |
| AC3.7 | `src/processing/compositing.py` output → `_run_pipeline` input | `test_composite_dimensions_match_crop`, `test_cutout_to_pdf_pipeline` |
| AC3.8a | `static/js/editor.js` state, stored images | `test_undo_composite_restores_cutout` |
| AC3.8b | `static/js/editor.js` state | `test_undo_cutout_restores_crop`, `test_skip_editing_pipeline` |
| AC3.9 | `src/processing/cutout.py` | `test_cutout_on_sample_subjects` (integration) |

---

## Stage 0: Dependencies & Infrastructure

**Goal**: Add `rembg` dependency, create preset directory structure, update config
**Success Criteria**: `rembg` installed in venv, model pre-download script works, `static/presets/` exists, config constants added
**Status**: Not Started

### Changes

- Add `rembg>=2.0.50,<3.0` to `requirements.txt`
- Add constants to `src/config.py`:
  - `CUTOUT_MASK_BLUR_RADIUS: int = 3` — Gaussian blur radius for mask feathering
  - `CUTOUT_MORPH_KERNEL_SIZE: int = 5` — morphological kernel for edge cleanup
  - `COMPOSITE_MIN_SCALE: float = 0.25`
  - `COMPOSITE_MAX_SCALE: float = 2.0`
  - `PRESET_BACKGROUNDS_DIR: Path` — points to `static/presets/`
- Create `static/presets/` directory (initially empty — file-based presets added by user later)
- Add model download note to `README.md` setup section

---

## Stage 1: Backend — Cutout Processing

**Goal**: `CutoutProcessor` class that removes backgrounds and cleans masks
**Success Criteria**: Unit tests pass for RGBA output, mask smoothness, and edge feathering
**Status**: Not Started

### New File: `src/processing/cutout.py`

- `CutoutProcessor` class (stateless, follows `ImageEnhancer` pattern)
  - `remove_background(image: Image.Image) -> tuple[Image.Image, Image.Image]`
    - Calls `rembg.remove()` to get RGBA result
    - Extracts alpha channel, runs `_clean_mask()`, replaces alpha
    - Returns (RGBA subject image, grayscale mask as separate Image)
  - `_clean_mask(mask: np.ndarray) -> np.ndarray`
    - Morphological close then open (removes small holes / noise)
    - Gaussian blur for feathering edges
    - Uses config constants for kernel size and blur radius

### Tests: `tests/test_cutout.py`

| Test | AC |
|------|-----|
| `test_cutout_produces_rgba` — output has 4 channels, alpha is non-trivial | AC3.1 |
| `test_cutout_returns_mask` — separate grayscale mask returned, same dimensions | AC3.1 |
| `test_cutout_mask_is_smooth` — no jagged edges (edge gradient variance check) | AC3.2 |
| `test_cutout_mask_feathered` — alpha values between 0–255 exist at edges | AC3.2 |

---

## Stage 2: Backend — Background Provider

**Goal**: `BackgroundProvider` that serves both programmatic and file-based backgrounds
**Success Criteria**: Unit tests confirm programmatic solids/gradients generate correct images; file-based presets loaded if present
**Status**: Not Started

### New File: `src/processing/backgrounds.py`

- `BackgroundInfo` dataclass: `id`, `name`, `type` ("programmatic" | "preset"), `colors` (for programmatic)
- `BackgroundProvider` class
  - `list_backgrounds() -> list[BackgroundInfo]` — combined list of programmatic + file scan
  - `get_background(background_id: str, width: int, height: int) -> Image.Image`
    - Programmatic: generates solid or gradient at exact (width, height)
    - File-based: loads from `PRESET_BACKGROUNDS_DIR`, scale-to-fill + center-crop to (width, height)
  - `_generate_solid(color: tuple[int,int,int], width: int, height: int) -> Image.Image`
  - `_generate_gradient(color_top: tuple, color_bottom: tuple, width: int, height: int) -> Image.Image`
    - Uses `np.linspace()` to interpolate between two colors vertically
- Programmatic backgrounds (hard-coded registry):
  - Solids: white, light gray, sky blue, pale yellow, mint green, light pink
  - Gradients: blue-to-white, sunset (orange-to-pink), forest (dark green-to-light green)
- File-based: scans `static/presets/` for `^[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$` — rejects anything else (path traversal defense)

### Tests: `tests/test_backgrounds.py`

| Test | AC |
|------|-----|
| `test_programmatic_backgrounds_list` — returns expected count and types | AC3.3 |
| `test_programmatic_solid_generates_correct_color` — white bg pixels are (255,255,255) | AC3.3 |
| `test_programmatic_gradient_has_color_range` — top and bottom rows differ | AC3.3 |
| `test_background_dimensions_match_request` — output matches requested w×h | AC3.3 |
| `test_preset_file_backgrounds` — file-based presets discovered from directory | AC3.3 |
| `test_preset_filename_validation` — rejects files with invalid names | Security |
| `test_custom_bg_resized_to_fill` — small bg scaled up, large bg center-cropped | AC3.4 |

---

## Stage 3: Backend — Compositing

**Goal**: `Compositor` class that places cutout subject onto background at specified position/scale
**Success Criteria**: Unit tests confirm correct positioning, scaling, dimension matching, and edge clipping
**Status**: Not Started

### New File: `src/processing/compositing.py`

- `Compositor` class (stateless)
  - `composite(subject: Image.Image, background: Image.Image, x: int, y: int, scale: float) -> Image.Image`
    - Validates/clamps scale to `COMPOSITE_MIN_SCALE`–`COMPOSITE_MAX_SCALE`
    - Scales subject (RGBA) using `Image.resize()` with `LANCZOS`
    - Alpha-composites onto background (RGB) at (x, y) using `Image.paste()` with alpha mask
    - Clips to canvas bounds (no crash if subject extends beyond edges)
    - Returns RGB image with same dimensions as background

### Tests: `tests/test_compositing.py`

| Test | AC |
|------|-----|
| `test_composite_subject_position` — subject placed at specified (x,y) offset | AC3.5 |
| `test_composite_subject_scale` — subject dimensions match scale factor | AC3.5 |
| `test_composite_scale_bounds` — scale outside 0.25–2.0 is clamped | AC3.5 |
| `test_composite_dimensions_match_background` — output same size as background | AC3.7 |
| `test_composite_output_is_rgb` — no alpha channel in final output | AC3.7 |
| `test_composite_subject_overflow_clipped` — subject extending beyond canvas is clipped, no error | Edge case |
| `test_composite_zero_offset` — subject at (0,0) renders in top-left | Baseline |

---

## Stage 4: Backend — API Endpoints

**Goal**: Three new endpoints integrated into `src/api/routes.py`
**Success Criteria**: Integration tests pass for all endpoints; validation rejects bad input
**Status**: Not Started

### Schema Changes: `src/api/schemas.py`

New models:
- `CutoutRequest(image_id: str)`
- `CutoutResponse(cutout_image_id: str, width: int, height: int)`
- `BackgroundInfoSchema(id: str, name: str, type: str, thumbnail_url: str | None)`
- `BackgroundListResponse(backgrounds: list[BackgroundInfoSchema])`
- `CompositeRequest(cutout_image_id: str, background_id: str, x: int = 0, y: int = 0, scale: float = 1.0)` with scale validator
- `CompositeResponse(composite_image_id: str, width: int, height: int)`

### Route Changes: `src/api/routes.py`

New endpoints:
- `POST /api/cutout`
  - Validates `image_id` with `_validate_id()`
  - Loads stored image via `_load_stored_image()`
  - Runs `CutoutProcessor.remove_background()` via `asyncio.to_thread()`
  - Saves RGBA result at `TEMP_DIR/{cutout_id}/cutout.png`
  - Also saves the original image_id reference for undo support
  - Returns `CutoutResponse`

- `GET /api/backgrounds`
  - Calls `BackgroundProvider.list_backgrounds()`
  - Returns `BackgroundListResponse`

- `POST /api/composite`
  - Two forms: JSON body (preset background_id) or multipart (custom background upload)
  - Validates cutout_image_id, loads RGBA cutout
  - Loads or generates background via `BackgroundProvider.get_background()`
  - For custom upload: validates with `_validate_image_bytes()`, same size limits
  - Runs `Compositor.composite()` via `asyncio.to_thread()`
  - Saves RGB result as `TEMP_DIR/{composite_id}/image.png` (same pattern as crop — pipeline-compatible)
  - Returns `CompositeResponse`

- `GET /api/cutout/{cutout_id}/image`
  - Returns the cutout RGBA PNG for frontend display

### Storage Pattern

- Cutout RGBA: `TEMP_DIR/{cutout_id}/cutout.png`
- Composite RGB: `TEMP_DIR/{composite_id}/image.png` (matches crop output — transparent to pipeline)

### Tests: `tests/test_image_editing_integration.py`

| Test | Description |
|------|-------------|
| `test_cutout_endpoint` | POST valid image_id → 200 + cutout_image_id |
| `test_cutout_invalid_id` | POST bad ID → 400 |
| `test_cutout_nonexistent_image` | POST missing ID → 404 |
| `test_backgrounds_endpoint` | GET → 200 + non-empty list with expected fields |
| `test_composite_with_preset_bg` | POST cutout_id + background_id + position/scale → 200 |
| `test_composite_with_custom_upload` | POST cutout_id + uploaded file → 200 |
| `test_composite_invalid_cutout_id` | POST bad cutout ID → 400 |
| `test_cutout_to_pdf_pipeline` | Upload → crop → cutout → composite → process → PDF → all 200 |
| `test_skip_editing_pipeline` | Upload → crop → process (no cutout) → PDF → all 200 (existing flow unbroken) |

---

## Stage 5: Frontend — Editor UI

**Goal**: New editor step between crop and process with cutout, background picker, position/scale, and two-level undo
**Success Criteria**: Manual QA scenarios QA1–QA8 pass
**Status**: Not Started

### New File: `static/js/editor.js`

Editor state machine: `idle` → `cutting` → `cut` → `compositing` → `composited`

- **Cutout button**: calls `POST /api/cutout`, displays RGBA result with CSS checkerboard transparency pattern
- **Background picker**: fetches `GET /api/backgrounds`, renders thumbnail grid; click selects
- **Custom background upload**: file input with same validation as main upload
- **Position**: vanilla JS pointer events (`pointerdown`/`pointermove`/`pointerup`) on a canvas overlay for drag interaction; sends (x, y) pixel offsets
- **Scale**: `<input type="range">` slider (0.25–2.0, step 0.05, default 1.0)
- **"Apply Composite" button**: calls `POST /api/composite`; stores `composite_image_id` in app state
- **Preview**: shows composite result in-place before proceeding
- **Undo composite**: reverts to cutout + background picker (clears composite, keeps cutout_image_id)
- **Undo cutout**: reverts to original crop (clears cutout_image_id, hides editor panel)
- **Skip button**: proceeds directly to process step (bypasses entire editor)
- **Continue button**: passes `composite_image_id` (or `cropped_image_id` if skipped) to step-process

### Modifications to Existing Files

- `static/index.html` — new `<section id="step-edit">` between step-crop and step-process
- `static/js/app.js` — after crop success, show step-edit instead of step-process; editor's "Continue" sets image ID for process step; update `showStep()` to include step-edit; update restart to clear editor state
- `static/css/style.css` — styles for editor panel, background thumbnail grid, checkerboard transparency pattern, drag overlay, scale slider, undo buttons

### QA Manual Test Scenarios

| # | Scenario | Steps | Expected |
|---|----------|-------|----------|
| QA1 | Cutout activation | Upload → crop → click "Cut Out Subject" | Subject isolated; checkerboard background visible |
| QA2 | Preset backgrounds | After cutout, click preset thumbnails | Background changes in preview |
| QA3 | Custom background | After cutout, upload custom image | Custom image behind subject |
| QA4 | Position and scale | Drag subject; adjust slider | Subject moves and resizes |
| QA5 | Apply and proceed | Click "Apply", then "Continue" | Mosaic generates from composite |
| QA6 | Undo composite | After applying, click "Undo Composite" | Returns to cutout + background picker |
| QA7 | Undo cutout | After cutout, click "Undo Cutout" | Returns to original crop; editor hidden |
| QA8 | Skip editing | After crop, click "Skip" | Process step shown; works as Phase 1 |

---

## Edge Cases & Error Handling

| Scenario | Handling |
|----------|----------|
| No clear foreground subject | Show mask preview overlay so user can evaluate; provide "Undo Cutout" |
| Subject touching crop edges | Display tip text: "For best results, crop with margin around subject" |
| Custom background smaller than crop | Scale-to-fill (resize preserving aspect ratio, center-crop to match) |
| Custom background larger than crop | Center-crop to match crop dimensions |
| Scale causes subject overflow | Clip to canvas; warn if >30% clipped |
| `rembg` model not downloaded | Show loading indicator "Downloading AI model (first time only)..." |
| Invalid custom background upload | Same validation as photo upload; show error message |

## Security Considerations

- Custom background uploads: same `_validate_image_bytes()` magic-byte check, same size limit, same `_load_image()` path
- Preset filenames validated with `^[a-zA-Z0-9_-]+\.(png|jpg|jpeg)$` — no path traversal
- All new IDs: `uuid.uuid4().hex` validated with `_UUID_HEX_RE`
- `rembg` runs locally — no data sent externally
- New endpoints behind same CORS + CSP middleware as existing routes

## Observability

- Log `rembg` inference time at INFO (matches pipeline logging pattern)
- Log composite parameters (position, scale, background type) at INFO
- Log model download if triggered (at WARNING — first-time event)
- Existing request logging covers new endpoints automatically
