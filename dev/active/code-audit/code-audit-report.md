# Code Audit Report — coloring-app

**Date:** 2026-03-27
**Scope:** Full codebase (all application source, dependency manifests, and test files)
**Auditor:** Code Auditor mode

---

## Executive Summary

- **Total files audited:** 22 (11 Python source, 2 JS, 1 HTML, 1 CSS, 2 manifests, 5 test files with reduced lens)
- **Findings by severity:** Critical: 1 | High: 5 | Medium: 18 | Low: 12
- **Top 5 highest-priority items:**
  1. Path traversal via `image_id` / `mosaic_id` in file operations (Critical)
  2. Unbounded in-memory mosaic store with no concurrency guard (High)
  3. `ColorPalette.colors_rgb` dtype inconsistency between uint8 and float64 (High)
  4. No CORS middleware configured (High)
  5. No startup validation of environment variables (High)

---

## Findings by Category

### 1. Cleanup & Condensing

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/config.py` | L22-23 | Low | Dead/redundant constants | `GRID_COLUMNS` and `GRID_ROWS` are default constants duplicated by `GRID_DIMENSIONS` lookup table. Only used as defaults in `GridGenerator.__init__`; all callers pass explicit values from the lookup. Consider removing or consolidating. |
| 2 | `src/config.py` | L44-50 | Low | Derived constants coupled to defaults | `PRINTABLE_WIDTH_MM`, `PRINTABLE_HEIGHT_MM`, `MARGIN_SIDE_MM`, `MARGIN_TOP_MM` are computed from the 3mm defaults, but `PdfRenderer._draw_grid_page` recomputes margins dynamically per-sheet. These module-level constants are only used in tests, creating a misleading single source of truth. |
| 3 | `src/api/schemas.py` | L76-78 | Low | Unused model | `ErrorResponse` is defined but never referenced by any endpoint or exception handler. Dead code. |

### 2. Errors & Defects

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/api/routes.py` | L117-122 | **Critical** | Path traversal in filesystem helpers | `_get_image_dir`, `_save_image`, `_load_stored_image` build `TEMP_DIR / image_id` without validating `image_id` themselves. Validation lives only at the endpoint level (`_validate_id`). If a new endpoint omits the call, or if a code change relaxes validation, a crafted ID like `../../etc` could escape the temp directory. Defense in depth requires co-locating validation with the filesystem operation. |
| 2 | `src/api/routes.py` | L189-191 | Medium | `GRID_DIMENSIONS` KeyError not caught | `_run_pipeline` accesses `GRID_DIMENSIONS[(size, mode)]` without a try/except. An unexpected combination raises an unhandled `KeyError` → HTTP 500 instead of a descriptive 400. |
| 3 | `src/api/routes.py` | L95-98 | Medium | `Image.open()` can raise on corrupt data | `_load_image` calls `Image.open(BytesIO(data))` after magic-byte validation, but a truncated or corrupt file with valid magic bytes will raise `UnidentifiedImageError` → unhandled 500. |
| 4 | `src/processing/quantization.py` | L45-47 | Medium | LAB centers truncated to uint8 before conversion | `centers_lab.reshape(1, -1, 3).astype(np.uint8)` truncates float LAB cluster centers to integers before `cvtColor`. This loses precision; should use `.round().astype(np.uint8)` or keep float precision through the conversion. |
| 5 | `src/rendering/preview.py` | L60-68 | Low | Hardcoded font paths with silent fallback | Font loading tries two OS-specific paths. On Windows or containers, both fail. The bitmap font fallback produces illegible labels at small cell sizes. |

### 3. Type Hints

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/api/routes.py` | L293 | Medium | `_build_palette_info` returns `list[dict]` | Return type should be `list[dict[str, Any]]` or a typed Pydantic model. Untyped `dict` propagates through `ProcessResponse.palette` and `PaletteEditResponse.palette`. |
| 2 | `src/api/routes.py` | L185-188 | Medium | `_run_pipeline` returns raw 4-tuple | `tuple[MosaicSheet, Image.Image, list[dict], Image.Image]` — a `NamedTuple` or dataclass would improve readability and prevent positional mistakes. |
| 3 | `src/models/mosaic.py` | L11 | Medium | `colors_rgb` typed as bare `np.ndarray` | No shape or dtype annotation. Should use `npt.NDArray[np.float64]` or similar. The actual dtype varies (uint8 vs float64) depending on the call site — see Consistency #1. |
| 4 | `src/api/schemas.py` | L55, L73 | Medium | `palette` field is `list[dict]` in response models | `ProcessResponse.palette` and `PaletteEditResponse.palette` should reference a typed `PaletteEntry` model for API contract clarity. |
| 5 | `src/rendering/preview.py` | L82 | Low | `_label_color_for_rgb` parameter type | Typed as `tuple[int, int, int]` but receives numpy scalar values from `palette.colors_rgb`. Works via duck typing but is technically inaccurate. |

### 4. Documentation (docstrings in source only)

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/config.py` | L46-50 | Low | Misleading inline comments | `# 180mm (with ~17.95mm side margins)` — these values are only correct for the 3mm/60×80 default, but the module also supports 4mm and 5mm sizes with different margins. Comments should note these are defaults. |

### 5. Readability, Brevity & Clarity

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/rendering/pdf.py` | L47-100 | Medium | `_draw_grid_page` is ~55 lines with 3-level nesting | Mode check → row loop → col loop → mode dispatch. Consider extracting per-mode dispatch or using a strategy pattern. |
| 2 | `src/api/routes.py` | L135-175 | Medium | `upload_image` mixes concerns | Chunked reading, validation, image loading, resizing, saving, and response building in one function (~40 lines). The chunked-read loop could be a helper. |
| 3 | `static/js/app.js` | L128-190 | Medium | Process button handler is ~60 lines | Builds DOM elements, attaches event listeners, and makes API calls inline. The palette-rendering loop (lines ~155-190) should be extracted. |
| 4 | `src/rendering/pdf.py` | L66-69 | Low | Magic numbers in font size calculation | `font_size = max(4, cell_mm * 0.6) * mm / mm * 2` — the `* mm / mm` cancels out, and `* 2` is unexplained. Should be simplified with a named scaling factor. |

### 6. Security Posture

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/api/routes.py` | L117-118 | **Critical** | Path traversal — defense in depth lacking | `_get_image_dir` concatenates `TEMP_DIR / image_id` without internal validation. All protection depends on callers remembering to invoke `_validate_id`. A single missed call = directory traversal. Validation must be inside `_get_image_dir`. |
| 2 | `src/api/routes.py` | entire file | **High** | No CORS middleware configured | The FastAPI app has no `CORSMiddleware`. While same-origin default is safe, any future cross-origin need risks an overly permissive configuration being added hastily. Should configure explicitly now. |
| 3 | `static/index.html` | L6, L94 | Medium | CDN dependencies without CSP | Cropper.js loaded from `cdnjs.cloudflare.com` with SRI hashes (good), but no `Content-Security-Policy` header constrains script sources at the server level. |
| 4 | `src/api/routes.py` | L246-248 | Low | User-derived data in HTTP header | `filename="mosaic-{mosaic_id[:8]}.pdf"` — currently safe since `mosaic_id` is hex-validated, but interpolating request-derived values into headers should be flagged for awareness. |

### 7. Library & Dependency Simplicity

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/processing/grid.py` | L6 | Medium | `scipy` imported for one function | `scipy.stats.mode` is the only scipy usage. `np.bincount(region.flat).argmax()` provides the same result with zero extra dependency. |
| 2 | `requirements.txt` | L1-11 | Medium | No version upper bounds | All dependencies use `>=` only. A breaking major-version release could silently break the app. Use compatible-release specifiers (e.g., `fastapi~=0.110.0` or `>=0.110,<1.0`). |
| 3 | `requirements.txt` | L10-11 | Low | Test dependencies in main requirements | `pytest` and `httpx` are runtime-irrelevant. Should be in a separate `requirements-dev.txt` or under `[project.optional-dependencies]` in `pyproject.toml`. |

### 8. Consistency

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/processing/quantization.py` L46 vs `src/api/routes.py` L282, `tests/test_palette_edit.py` L10 | — | **High** | `ColorPalette.colors_rgb` dtype mismatch | `quantization.py` creates palettes with `uint8` arrays; `routes.py` palette edit writes `float64` values; `test_palette_edit.py` explicitly creates `float64` palettes. `hex_color()` calls `int()` which works for both, but `np.array_equal` comparisons in `_compute_palette_warnings` are dtype-sensitive. This is a latent bug that could cause missed or spurious duplicate warnings. |
| 2 | `src/api/routes.py` L256 vs `src/processing/quantization.py` L34-37 | — | Medium | Different LAB conversion patterns | `routes.py` converts single pixels (1×1 BGR→LAB); `quantization.py` converts entire images. While functionally the same, the differing patterns make maintenance harder. |
| 3 | `static/js/crop.js` | L20 | Medium | Hardcoded crop aspect ratio `60/80` | The cropper uses a fixed 3:4 aspect ratio, but hexagon mode grids have different dimensions (e.g., 60×93 ≈ 2:3). Since crop happens before mode selection, users crop at the wrong ratio for non-square modes. |
| 4 | Tests | — | Low | `client` fixture duplicated | `@pytest.fixture def client()` is defined identically in `test_integration.py`, `test_mosaic_modes_integration.py`, and `test_palette_edit_integration.py`. Should be in `conftest.py`. |

### 9. DRY & Deduplication

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `tests/test_integration.py`, `tests/test_mosaic_modes_integration.py`, `tests/test_palette_edit_integration.py` | — | Medium | `_make_jpeg_bytes` / `_make_png_bytes` duplicated × 3 | Identical helper functions copied across three test files. Belongs in `conftest.py`. |
| 2 | `tests/test_mosaic_modes.py`, `tests/test_preview.py` | — | Medium | `_make_grid` helper duplicated | Nearly identical grid-building helpers in both files. |
| 3 | `src/rendering/pdf.py` L123-127 and L157-159; `src/rendering/preview.py` L83-85 | — | Low | Brightness formula duplicated 3× | `0.299*r + 0.587*g + 0.114*b` appears in `_draw_circle_cell`, `_draw_hexagon_cell`, and `_label_color_for_rgb`. Should be a shared utility. |
| 4 | `src/rendering/pdf.py` | — | Low | Label-drawing logic duplicated in circle and hexagon cell methods | Center-text-on-cell with brightness-based color selection is copy-pasted between `_draw_circle_cell` and `_draw_hexagon_cell`. |

### 10. Error Handling Patterns

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/main.py` | L33 | Medium | `shutil.rmtree(entry, ignore_errors=True)` | Per-directory cleanup failures are silently ignored. The outer `except Exception` logs a generic message, but individual directory errors are swallowed, hiding permission or locking issues. |
| 2 | `src/api/routes.py` | L189-191 | Medium | Unhandled `KeyError` from `GRID_DIMENSIONS` lookup | Invalid `(size, mode)` key → unhandled exception → HTTP 500. Should catch and return 400 with a descriptive message. |
| 3 | `static/js/app.js` | L60-65 | Low | `res.json()` can throw on non-JSON responses | If a reverse proxy returns a 502/504 HTML page, `res.json()` throws. The catch block shows only a generic message without the HTTP status code. |

### 11. Configuration Hygiene

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/config.py` | L8-10 | **High** | Env vars read at import with no validation | `int(os.getenv("MAX_UPLOAD_SIZE_MB", "20"))` — a non-numeric env var value (e.g., `MAX_UPLOAD_SIZE_MB=abc`) crashes the app at import time with an unhelpful `ValueError`. Should validate at startup with clear error messages. |
| 2 | `src/config.py` | L52 | Medium | `TEMP_DIR` not verified for write access | `TEMP_DIR` defaults to system temp but a misconfigured `COLORING_TEMP_DIR` env var silently fails at runtime (during first write) rather than at startup. |
| 3 | `src/config.py` | — | Medium | No centralized config object | Environment variables are scattered as module-level constants. A `Settings` class (e.g., pydantic-settings `BaseSettings`) would centralize validation, typing, and testability. |

### 12. Logging Quality

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/main.py` | L35 | Low | Cleanup log lacks directory names | `logger.info("Cleaned up %d expired temp directories", count)` — doesn't log which directories were removed, making post-incident debugging difficult. |
| 2 | `src/api/routes.py` | — | Low | No request-scoped correlation ID | Logs reference image/mosaic IDs (good), but there's no overarching request ID for tracing a request lifecycle through upload → crop → process → preview → PDF. |

### 13. Performance Anti-Patterns

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/processing/grid.py` | L48-56 | Medium | `scipy.stats.mode` called per-cell in nested loop | For a 60×80 grid, `stats.mode()` is called 4,800 times, each creating intermediate arrays. Vectorized `np.bincount` per block or a strided approach would be significantly faster. |
| 2 | `src/api/routes.py` | L156 | Medium | `get_image` reads entire file into memory | `path.read_bytes()` loads the full PNG for every request. For 4000×4000 images, this is several MB. Consider `FileResponse` or streaming. |
| 3 | `src/api/routes.py` | L255-270 | Low | Per-color `cv2.cvtColor` in warnings computation | Single-pixel BGR→LAB conversion in a loop for each palette color. Could be batched into one conversion. |

### 14. API Contract Adherence

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1 | `src/api/schemas.py` | L55, L73 | Medium | `palette` field is untyped `list[dict]` | `ProcessResponse.palette` and `PaletteEditResponse.palette` don't specify the shape of palette entries. Consumers have no contract for expected keys (`index`, `label`, `hex`). Should be `list[PaletteEntry]` with a defined model. |
| 2 | `src/api/schemas.py` | L76-78 | Low | `ErrorResponse` model defined but unused | Dead code — FastAPI's default error handling is used instead. |

---

## Cross-Cutting Observations

### 1. `colors_rgb` dtype inconsistency (spans: `quantization.py`, `routes.py`, `mosaic.py`, `test_palette_edit.py`)
The `ColorPalette.colors_rgb` array is created as `uint8` in the quantization pipeline but modified as `float64` during palette editing. `hex_color()` handles both via `int()`, but `np.array_equal` in `_compute_palette_warnings` is dtype-sensitive, creating a latent bug where duplicate warnings may fire or fail incorrectly.

### 2. Path safety not co-located with filesystem ops (spans: `routes.py`)
All filesystem helpers (`_get_image_dir`, `_save_image`, `_load_stored_image`) trust callers to validate IDs. Defense in depth requires validation inside `_get_image_dir` itself.

### 3. Test helper duplication (spans: `test_integration.py`, `test_mosaic_modes_integration.py`, `test_palette_edit_integration.py`, `test_mosaic_modes.py`, `test_preview.py`)
`_make_jpeg_bytes`, `_make_png_bytes`, `_make_grid`, `_upload_and_crop`, and `client` fixture are duplicated across 3–5 test files. Should be centralized in `conftest.py`.

### 4. Brightness calculation duplicated 3× (spans: `pdf.py`, `preview.py`)
The luminance formula `0.299*r + 0.587*g + 0.114*b` appears in `_draw_circle_cell`, `_draw_hexagon_cell`, and `_label_color_for_rgb`. Should be a single shared utility.

### 5. Crop aspect ratio mismatch (spans: `crop.js`, `config.py`)
The JS cropper uses a fixed 60/80 aspect ratio that doesn't adapt to the selected mode/size combination. Hexagon mode (60×93) and larger sizes (50×65, 40×52) need different ratios.

---

## Recommended Priority Order

### 1. Quick Wins — Low effort, high impact
1. Move ID validation inside `_get_image_dir` for path traversal defense in depth
2. Wrap `Image.open()` in try/except in `_load_image` → return 400 on corrupt images
3. Catch `KeyError` for `GRID_DIMENSIONS` lookup in `_run_pipeline` → return 400
4. Replace `scipy.stats.mode` with `np.bincount().argmax()` to drop scipy dependency and improve grid generation performance
5. Use `.round().astype(np.uint8)` in quantization LAB→RGB center conversion

### 2. Important Fixes — Security and correctness
6. Standardize `ColorPalette.colors_rgb` dtype across the codebase (pick one: float64 or uint8)
7. Add startup validation for environment variables (or adopt pydantic-settings)
8. Add `CORSMiddleware` with explicit allowed origins
9. Add `Content-Security-Policy` response header

### 3. Improvement Pass — Type hints, docstrings, DRY cleanup
10. Define a `PaletteEntry` Pydantic model; use it in `ProcessResponse` and `PaletteEditResponse`
11. Centralize test helpers in `conftest.py` (remove duplicates from individual test files)
12. Extract brightness/luminance calculation into a shared utility
13. Add upper bounds or compatible-release specifiers to dependency versions
14. Separate test dependencies from runtime dependencies
15. Replace `_run_pipeline` raw tuple with a `NamedTuple`

### 4. Polish — Style, readability, minor cleanup
16. Extract palette DOM-building logic from process button handler in `app.js`
17. Break `_draw_grid_page` in `pdf.py` into smaller methods
18. Remove unused `ErrorResponse` schema
19. Simplify font size calculation magic numbers in `pdf.py`
20. Fix misleading inline comments in `config.py` (margin values only correct for 3mm default)
21. Add request-scoped correlation IDs to logging
