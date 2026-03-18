# Phase 1 Code Review (v2)

**Reviewer**: Plan Reviewer  
**Date**: 2026-03-17  
**Scope**: All Phase 1 files — AC1.1 through AC1.10  
**Plan document**: `docs/phases/PHASE_1_CORE_PIPELINE.md`  
**Prior review**: v1 (2026-03-17) — all 12 issues from v1 have been resolved; this is a fresh re-review.

---

## Prior Issues — Resolution Status

All 12 issues from the v1 review have been addressed:

| v1 # | Issue | Resolution |
|-------|-------|------------|
| 1 | Crop coordinate mismatch on large images | **Fixed.** Frontend now loads stored (resized) image via `GET /api/image/{id}` for cropping (`app.js:69`, `routes.py:179-184`). |
| 2 | Sync CPU blocks event loop | **Fixed.** `_run_pipeline` called via `asyncio.to_thread()` (`routes.py:288`). |
| 3 | Unbounded `_mosaic_store` | **Fixed.** `OrderedDict` capped at 100 entries with LRU eviction (`routes.py:45-46`, `routes.py:297-299`). |
| 4 | Full file read before size check | **Fixed.** Chunked 8KB reads with early abort (`routes.py:149-160`). |
| 5 | `scipy` missing from requirements | **Fixed.** `scipy>=1.12.0` added to `requirements.txt`. |
| 6 | No path-traversal guard | **Fixed.** `_validate_id` with `^[a-f0-9]{32}$` regex (`routes.py:50-58`). |
| 7 | No test for PDF grid dimensions | **Fixed.** `test_pdf_grid_page_dimensions` added (`test_pdf.py:56-73`). |
| 8 | No preview unit tests | **Fixed.** `test_preview.py` added with 3 tests (dimensions, mode, color match). |
| 9 | Cumulative timing only | **Fixed.** Per-step timing in `_run_pipeline` (`routes.py:234-250`). |
| 10 | Silent font fallback | **Fixed.** `logger.warning()` on fallback (`preview.py:55`). |
| 11 | Unused `LABEL_CHARS` import | **Fixed.** Import removed from `quantization.py`. |
| 12 | PDF grid height 260mm vs 263.5mm | **Clarified.** Test asserts `260.0mm` grid height; deviation documented in implementation summary. |

---

## Top Risks (max 5)

1. **No temp-file cleanup/TTL** — Every upload, crop, and process creates directories under `TEMP_DIR` that are never deleted. Disk usage grows without bound during long-running sessions. The plan requires "Temp files cleaned up on configurable TTL."
2. **Evicted mosaics leave orphaned disk files** — When `_mosaic_store` evicts the oldest entry, the corresponding `TEMP_DIR/{id}/` directory (containing `image.png`, `preview.png`) is not deleted.
3. **PDF unreachable after store eviction or restart** — PDF generation depends entirely on `_mosaic_store` (in-memory). After server restart or eviction of the entry, `GET /api/pdf/{id}` returns 404 even though preview images persist on disk.
4. **Ruff lint failure in `test_preview.py`** — Import block is un-sorted, which will fail CI if ruff is enforced.
5. **`test_pdf_grid_page_dimensions` doesn't parse actual PDF layout** — The test only validates the arithmetic (`50*4=200`, `65*4=260`) and that the output starts with `%PDF-`. It does not parse the rendered PDF to verify the grid bounding box on the page.

---

## Issue Table

| # | Issue | Severity | Evidence | Requirement | Recommendation |
|---|-------|----------|----------|-------------|----------------|
| 1 | **No temp-file cleanup.** Directories under `TEMP_DIR` for uploads, crops, and mosaics are never deleted. In a long-running session or under load, disk usage will grow unbounded. | **High** | `routes.py` — `_save_image` creates dirs; `main.py` lifespan only `mkdir`s; no cleanup code anywhere. | Plan: "Temp files cleaned up on configurable TTL" | Add a background task or lifespan shutdown hook that deletes directories older than a configurable TTL. |
| 2 | **Orphaned disk files on mosaic eviction.** When `_mosaic_store.popitem(last=False)` evicts an entry, the corresponding disk files remain. | **Med** | `routes.py:297-299` — eviction pops the OrderedDict entry but does not `shutil.rmtree` the directory. | Plan: temp file cleanup | When evicting a store entry, also delete `TEMP_DIR / evicted_mosaic_id`. |
| 3 | **PDF unavailable after server restart.** Mosaic data lives only in `_mosaic_store` (process memory). A restart loses all mosaic data. Users who still have the preview page open will get 404 on PDF download. | **Med** | `routes.py:331-332` — `_mosaic_store.get(mosaic_id)` returns `None` after restart. | Plan doesn't specify persistence for Phase 1, but this creates a poor UX cliff. | Document as known limitation, or serialize `MosaicSheet` to disk alongside the preview. |
| 4 | **Ruff import-sorting lint error in `test_preview.py`.** Import block is unsorted per the project's ruff `I` (isort) rule. | **Low** | `get_errors` output for `test_preview.py:3` — `"Import block is un-sorted or un-formatted"` | Project quality: `pyproject.toml [tool.ruff.lint] select = ["E", "F", "I", "W"]` | Reorder imports to satisfy ruff. |
| 5 | **`test_pdf_grid_page_dimensions` doesn't verify rendered PDF.** Test checks `50*4=200` and `65*4=260` arithmetically but doesn't parse the PDF to verify the grid drawing commands produce those dimensions on the page. | **Low** | `test_pdf.py:56-73` — only arithmetic assertions + `%PDF-` header check. | AC1.10: "PDF grid fills the printable area" | Acceptable for Phase 1 POC. For stronger coverage, parse PDF content streams or use `pdfplumber` to verify rect positions. |
| 6 | **CDN-loaded Cropper.js without SRI hash.** `index.html` loads JS and CSS from `cdnjs.cloudflare.com` without `integrity` attributes. A CDN compromise could inject malicious code. | **Low** | `index.html:8,76` | Security best practices | Add `integrity` and `crossorigin` attributes, or vendor the library locally. |

---

## Quick Wins

1. **Fix import sort in `test_preview.py`** — reorder the import block to satisfy ruff.
2. **Delete disk files on mosaic eviction** — add `shutil.rmtree(TEMP_DIR / evicted_id, ignore_errors=True)` when evicting from `_mosaic_store`.
3. **Add SRI hashes to CDN script/link tags** — straightforward `integrity` attribute addition.

---

## Review Tasks Detail

### 1. Traceability

| AC | Status | Location |
|----|--------|----------|
| AC1.1 (Upload JPEG/PNG) | **Complete** | `routes.py:143-175`, `index.html:22-30` |
| AC1.2 (Zoom/crop) | **Complete** | `routes.py:179-216`, `crop.js`, `app.js:64-100`. Frontend loads server-stored image via `GET /api/image/{id}`, resolving the v1 coordinate mismatch. |
| AC1.3 (Enhancement) | **Complete** | `enhancement.py` |
| AC1.4 (Color count 8–20) | **Complete** | `schemas.py:36`, `index.html:47-51` |
| AC1.5 (K-means in LAB) | **Complete** | `quantization.py` |
| AC1.6 (Grid 50×65 at 4mm) | **Complete** | `grid.py`, `config.py:21-23` |
| AC1.7 (Single-char labels) | **Complete** | `config.py:17`, `mosaic.py:36-44` |
| AC1.8 (Preview) | **Complete** | `preview.py`, `routes.py:313-321` |
| AC1.9 (PDF: grid + legend) | **Complete** | `pdf.py` |
| AC1.10 (PDF fills printable area) | **Complete (with documented deviation)** | `pdf.py:54-75`, `config.py:24-28`. Grid is 200mm × 260mm; 3.5mm bottom margin documented. |

All 10 acceptance criteria are implemented.

### 2. Correctness & Bugs

No functional correctness bugs detected. The v1 blocker (crop coordinate mismatch) is resolved — the frontend now fetches the server-stored (possibly resized) image via `/api/image/{id}` and feeds it to Cropper.js, so coordinates always match.

Edge cases from the plan:
- **Transparent PNG** → RGB with white background ✅ (`routes.py:86-90`)
- **Very large image (> 4000px)** → resized, then served to frontend for cropping ✅ (`routes.py:96-108`, `routes.py:179-184`)
- **Monochrome/low-contrast** → K-means logs warning ✅ (`quantization.py:63-68`)
- **Very small crop (< 50px)** → rejected with descriptive error ✅ (`routes.py:204-208`)
- **Non-image file** → magic byte check ✅ (`routes.py:65-79`)
- **Oversized file** → chunked read with early abort ✅ (`routes.py:149-160`)
- **Concurrent uploads** → UUID directories ✅

### 3. Consistency

- Python code follows consistent patterns: OOP with small focused classes, `logging` throughout, config from `config.py`.
- Frontend follows a clean step-wizard pattern with consistent fetch/error-handling structure.
- API schemas use Pydantic `Field` constraints consistently.
- Naming conventions are uniform across modules: snake_case functions, PascalCase classes, ALL_CAPS constants.
- No internal inconsistencies detected.

### 4. Cleanliness

Code is well-structured. Each processing step is a single-purpose class with clear inputs and outputs. Data flows linearly from upload through PDF generation. Models are clean dataclasses.

- No dead code or unused imports detected (the v1 `LABEL_CHARS` issue was fixed).
- No unnecessary abstractions — complexity matches the problem.
- No duplication; each concern lives in exactly one module.
- One lint issue: unsorted imports in `test_preview.py` (Issue #4).

### 5. Completeness

| Concern | Status |
|---------|--------|
| Observability — per-step timing | ✅ Each step logged with individual duration in `_run_pipeline` |
| Observability — dimensions/counts | ✅ Logged at each step |
| Input validation | ✅ Upload size (chunked), magic bytes, crop bounds, color range, ID format |
| Path-traversal protection | ✅ `_validate_id` with hex UUID regex |
| Temp file cleanup/TTL | **Missing** (Issue #1) — plan requirement not met |
| Memory eviction | ✅ `_mosaic_store` capped at 100 with LRU eviction |
| Error handling | ✅ 400 for bad input, 404 for missing resources, descriptive messages |
| Configuration | ✅ All constants in `config.py`, env var overrides for key values |
| Async safety | ✅ CPU pipeline offloaded to thread via `asyncio.to_thread()` |

### 6. Tests

| AC | Tests Present | Coverage |
|----|---------------|----------|
| AC1.1 | `test_upload_valid_jpeg`, `test_upload_valid_png`, `test_upload_invalid_file`, `test_upload_oversized` | ✅ Good |
| AC1.2 | `test_crop_valid_region`, `test_crop_too_small`, `test_crop_out_of_bounds` | ✅ Good |
| AC1.3 | `test_enhancement_increases_contrast`, `test_enhancement_increases_saturation`, `test_enhancement_preserves_dimensions`, `test_enhancement_returns_rgb` | ✅ Good |
| AC1.4 | Validated by Pydantic + integration test | ✅ Adequate |
| AC1.5 | `test_quantization_returns_requested_colors`, `test_quantization_label_map_shape`, `test_quantization_label_map_values`, `test_quantization_uses_lab_space`, `test_quantization_reproducible` | ✅ Good |
| AC1.6 | `test_grid_dimensions_4mm`, `test_grid_cell_coordinates` | ✅ Good |
| AC1.7 | `test_grid_all_cells_have_labels`, `test_grid_labels_8_colors`, `test_grid_labels_20_colors` | ✅ Good |
| AC1.8 | `test_preview_dimensions`, `test_preview_is_rgb`, `test_preview_colors_match_palette` | ✅ Good |
| AC1.9 | `test_pdf_two_pages`, `test_pdf_is_valid`, `test_pdf_legend_has_all_colors`, `test_pdf_different_color_counts` | ✅ Good |
| AC1.10 | `test_pdf_grid_page_dimensions` (arithmetic + valid PDF) | ✅ Adequate (see Issue #5 for stronger coverage) |

**Total**: 30 tests passing across 6 test modules. All 10 ACs have test coverage.

**Highest-value tests to add (nice-to-have):**
1. `test_upload_large_image_resized` — upload a > 4000px image, verify returned dimensions are scaled down, then crop succeeds with coordinates against the resized image.
2. `test_mosaic_store_eviction` — process > 100 mosaics, verify oldest entries are evicted and don't cause errors.
3. `test_process_concurrent_requests` — verify two concurrent process requests don't interfere (thread-safety sanity check).
