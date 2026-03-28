# Codebase Context

Dense reference for AI agents working in this repository.

## Identity

- **What**: Mosaic color-by-number coloring sheet generator
- **Stack**: Python 3.12 / FastAPI backend, vanilla HTML/JS/CSS frontend, no build step
- **Entry point**: `src/main.py` → `uvicorn src.main:app`
- **Test runner**: `pytest` (configured in `pyproject.toml`, test path `tests/`)

## Folder Structure

```
src/
  main.py              # FastAPI app, lifespan (temp dir + cleanup task), CORS + CSP middleware
  config.py            # All constants; env-var overrides; validate_config() at startup
  api/
    routes.py          # All endpoints; in-memory OrderedDict mosaic store (_mosaic_store)
    schemas.py         # Pydantic models; MosaicMode enum; hex color validator
  models/
    mosaic.py          # ColorPalette, GridCell, MosaicSheet dataclasses
  processing/
    enhancement.py     # ImageEnhancer: CLAHE + saturation + sharpening
    quantization.py    # ColorQuantizer: K-means in CIELAB via sklearn
    grid.py            # GridGenerator: label map → 2D GridCell list
  rendering/
    preview.py         # PreviewRenderer: PIL-based PNG with square/circle/hex cells
    pdf.py             # PdfRenderer: two-page US Letter PDF via ReportLab
    geometry.py        # hex_vertices(): pointy-top hexagon vertex math
    color_utils.py     # perceived_brightness(): BT.601 luminance
static/
  index.html           # Single-page UI, 4 steps toggled via hidden attribute
  js/app.js            # API calls, step state machine, palette edit with debounce
  js/crop.js           # CropManager class wrapping Cropper.js
tests/
  conftest.py          # Shared fixtures: client, sample_rgb_image, low_contrast_image, small_image
  test_integration.py  # Full API pipeline tests (upload → crop → process → preview → PDF)
  test_enhancement.py  # ImageEnhancer unit tests
  test_quantization.py # ColorQuantizer unit tests
  test_grid.py         # GridGenerator unit tests
  test_preview.py      # PreviewRenderer unit tests
  test_pdf.py          # PdfRenderer unit tests
  test_mosaic_modes*.py         # Circle and hexagon mode tests
  test_palette_edit*.py         # Palette editing tests
  test_audit_fixes.py  # Security/validation regression tests
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/upload` | Upload JPEG/PNG, returns `image_id` |
| GET | `/api/image/{image_id}` | Retrieve stored image |
| POST | `/api/crop` | Crop image, returns `cropped_image_id` |
| POST | `/api/process` | Run pipeline, returns `mosaic_id` + palette |
| GET | `/api/preview/{mosaic_id}` | Get mosaic preview PNG |
| GET | `/api/preview/{mosaic_id}/original` | Get pre-enhancement preview PNG |
| GET | `/api/pdf/{mosaic_id}` | Generate and download PDF |
| POST | `/api/palette/edit` | Edit one palette color, re-renders preview |

## Key Patterns

- **IDs are hex UUIDs** — `uuid.uuid4().hex` (32-char lowercase hex, no dashes). Validated with `_UUID_HEX_RE` regex in routes.
- **Images stored on disk** — under `TEMP_DIR/{id}/image.png`. Previews at `TEMP_DIR/{id}/preview.png`.
- **Mosaic sheets in memory** — `_mosaic_store: OrderedDict[str, MosaicSheet]`, max 100 entries, LRU eviction.
- **CPU work off event loop** — `asyncio.to_thread()` wraps `_run_pipeline` and palette re-render.
- **Pipeline order** — enhance → quantize → grid → preview render. Always this order.
- **Color labels** — single char from `LABEL_CHARS = "0123456789ABCDEFGHIJ"`. Max 20 colors.
- **Grid dimensions** — looked up from `GRID_DIMENSIONS` dict keyed by `(size_mm, mode)`. Not computed at runtime.
- **Validation** — magic bytes checked before PIL opens image; Pydantic validates all request bodies; `_validate_id()` guards every ID parameter.
- **Linting** — Ruff with rules E, F, I, W at line-length 100.
- **Tests** — `pytest`; `TestClient` from FastAPI for integration tests; NumPy fixtures for unit tests.

## Configuration Constants (config.py)

- `MAX_UPLOAD_SIZE_MB` / `MAX_UPLOAD_SIZE_BYTES` — upload cap
- `MAX_IMAGE_DIMENSION` — triggers downscale if exceeded
- `MIN_COLORS=8`, `MAX_COLORS=20` — palette bounds
- `GRID_DIMENSIONS` — `dict[(int, str), (int, int)]` mapping `(size, mode)` → `(cols, rows)`
- `PAPER_WIDTH_MM=215.9`, `PAPER_HEIGHT_MM=279.4` — US Letter
- `TEMP_DIR`, `TEMP_TTL_SECONDS`, `TEMP_CLEANUP_INTERVAL_SECONDS` — temp file lifecycle

## Naming Conventions

- Snake_case everywhere (Python, file names, test names)
- Private helpers prefixed with `_` (e.g., `_run_pipeline`, `_validate_id`, `_load_stored_image`)
- Test files match `test_{module}.py`; test functions match `test_{behavior}`
- Fixtures in `conftest.py`; no fixture files outside `tests/`
- Pydantic models use PascalCase class names, snake_case fields

## Mosaic Modes

| Mode | Shape | Grid behavior |
|------|-------|---------------|
| `square` | Rectangles filling the cell | Grid cells tile without gaps |
| `circle` | Circles with gap on black background | Same (cols, rows) as square |
| `hexagon` | Pointy-top hexagons, odd rows offset | Different (cols, rows) per size; uses `hex_vertices()` |

## Do Not

- Do not add a database — state is intentionally in-memory + temp disk for Phase 1
- Do not use two-character labels — cells are too small; max 20 colors enforced
- Do not skip magic-byte validation — PIL alone is not sufficient for upload security
- Do not run pipeline steps on the async event loop — always use `asyncio.to_thread()`
- Do not import from `tests/` in `src/`
- Do not add a frontend build step — the app uses vanilla JS loaded directly
- Do not install packages globally — always use the `.venv`
- Do not hardcode grid dimensions — always use the `GRID_DIMENSIONS` lookup table
- Do not use `--no-verify` to bypass git hooks
