# Phase 3: Image Editing Tools — Context

## Key Files

### Backend — Will Be Modified

| File | Current Role | Phase 3 Changes |
|------|-------------|-----------------|
| `src/config.py` | All app constants | Add cutout/composite/background constants |
| `src/api/routes.py` | All HTTP endpoints | Add `/api/cutout`, `/api/backgrounds`, `/api/composite`, `/api/cutout/{id}/image` |
| `src/api/schemas.py` | Pydantic request/response models | Add `CutoutRequest`, `CutoutResponse`, `CompositeRequest`, `CompositeResponse`, `BackgroundInfoSchema`, `BackgroundListResponse` |
| `requirements.txt` | Python dependencies | Add `rembg>=2.0.50,<3.0` |
| `README.md` | Setup docs | Add `rembg` model download note |

### Backend — New Files

| File | Purpose |
|------|---------|
| `src/processing/cutout.py` | `CutoutProcessor`: wraps `rembg`, mask cleanup (feathering, morphology) |
| `src/processing/backgrounds.py` | `BackgroundProvider`: programmatic solids/gradients + file-based preset scanning |
| `src/processing/compositing.py` | `Compositor`: alpha-composite subject onto background at position/scale |

### Frontend — Will Be Modified

| File | Phase 3 Changes |
|------|-----------------|
| `static/index.html` | Add `<section id="step-edit">` between crop and process |
| `static/js/app.js` | Route from crop → editor → process; pass composite/crop ID to process |
| `static/css/style.css` | Editor panel, background thumbnails, drag overlay, scale slider styles |

### Frontend — New Files

| File | Purpose |
|------|---------|
| `static/js/editor.js` | Editor UI: cutout button, background picker, drag-to-position, scale slider, undo |

### Test Files — New

| File | Purpose |
|------|---------|
| `tests/test_cutout.py` | Unit tests for `CutoutProcessor` |
| `tests/test_backgrounds.py` | Unit tests for `BackgroundProvider` |
| `tests/test_compositing.py` | Unit tests for `Compositor` |
| `tests/test_image_editing_integration.py` | Integration tests for new endpoints + full pipeline |

### Preset Assets — New Directory

| Path | Purpose |
|------|---------|
| `static/presets/` | Directory for user-added preset background images (initially empty; programmatic backgrounds don't need files) |

## Decisions

| Decision | Rationale |
|----------|-----------|
| `rembg` for background removal | Runs locally, no API key, good quality on common subjects, Python-native |
| Programmatic + file-based backgrounds | Programmatic: no asset management for simple solids/gradients; File-based: user can drop in custom presets later |
| Vanilla JS for drag interaction | Consistent with existing no-library frontend (only Cropper.js from CDN) |
| Two-level undo (composite / cutout) | Matches user mental model without undo stack complexity |
| Composite stored as `image.png` | Same path pattern as crop output — pipeline doesn't need to know about editing |
| Scale-to-fill for background resizing | Better than stretching (preserves aspect ratio); center-crop avoids empty areas |
| Cutout RGBA stored separately from composite | Allows undo-composite without re-running `rembg` |

## Constraints

- No build step for frontend (vanilla JS, CDN-only external libs)
- `rembg` U2-Net model is ~170MB — first use downloads it; must document
- Max 20 colors, single-character labels — unchanged from Phase 1
- Images stored on disk at `TEMP_DIR/{id}/` — same temp lifecycle and cleanup
- In-memory mosaic store — no database
- All CPU work must run via `asyncio.to_thread()`
- All IDs are `uuid.uuid4().hex` validated with `_UUID_HEX_RE`
- Linting: Ruff with E, F, I, W rules at line-length 100

## Patterns to Follow

### Processing classes (from `ImageEnhancer`, `ColorQuantizer`, `GridGenerator`)
- Stateless classes, class-level constants for tunable parameters
- Single public method that takes PIL Image / numpy array, returns result
- Private helper methods prefixed with `_`
- Logged timing at INFO level

### API endpoints (from existing routes)
- `_validate_id()` on every ID parameter
- `asyncio.to_thread()` for CPU-heavy work
- `_load_stored_image()` for loading by ID
- `_save_image()` for persisting results
- `_validate_image_bytes()` for upload validation
- Structured logging with timing

### Frontend (from `app.js`, `crop.js`)
- Step toggling via `hidden` attribute
- State object at module scope
- Separate JS file per concern (crop.js → editor.js)
- No framework, vanilla DOM manipulation
- CDN for external libraries only

### Tests (from existing test files)
- `conftest.py` for shared fixtures
- `TestClient` for integration tests
- NumPy/PIL fixtures for unit tests
- Helper functions like `make_jpeg_bytes()`, `upload_and_crop()` for common setup
- Test names: `test_{behavior}`

## Cross-References

- Spec: `docs/phases/PHASE_3/PHASE_3_IMAGE_EDITING.md`
- Architecture: `ARCHITECTURE.md`
- Codebase context: `CODEBASE_CONTEXT.md`
- Phase 1: `docs/phases/PHASE_1/PHASE_1_CORE_PIPELINE.md`
