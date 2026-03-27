# Implementation Record: Code Audit Fixes

## Summary
Implemented all 18 priority items from the code audit report, fixing 1 critical path traversal vulnerability, 5 high-severity issues, and 12 medium/low improvements across security, correctness, consistency, and DRY concerns.

## Acceptance Criteria Status

| AC | Description | Status | Implementing Files | Notes |
|----|-------------|--------|--------------------|-------|
| AC1 | Path traversal defense in depth | Done | `src/api/routes.py` | `_get_image_dir` now validates hex UUID internally |
| AC2 | Corrupt image handling | Done | `src/api/routes.py` | `_load_image` wraps `Image.open` + `.load()` in try/except |
| AC3 | KeyError guard for GRID_DIMENSIONS | Done | `src/api/routes.py` | `_run_pipeline` catches KeyError → HTTP 400 |
| AC4 | Drop scipy dependency | Done | `src/processing/grid.py`, `requirements.txt` | Replaced `scipy.stats.mode` with `np.bincount().argmax()` |
| AC5 | Fix quantization precision | Done | `src/processing/quantization.py` | Added `.round()` before `.astype(np.uint8)` |
| AC6 | Standardize colors_rgb dtype | Done | `src/api/routes.py`, `tests/test_palette_edit.py` | Palette edit writes uint8; tests use uint8; `_compute_palette_warnings` normalizes dtype |
| AC7 | Env var validation | Done | `src/config.py`, `src/main.py` | `_parse_int_env` + `validate_config()` called at startup |
| AC8 | Add CORS middleware | Done | `src/main.py` | `CORSMiddleware` with configurable origin via `CORS_ALLOWED_ORIGINS` env var |
| AC9 | Add CSP header | Done | `src/main.py` | `CSPMiddleware` restricts script/style sources |
| AC10 | Define PaletteEntry model | Done | `src/api/schemas.py` | Typed `PaletteEntry` replaces `list[dict]` in responses |
| AC11 | Centralize test helpers | Done | `tests/conftest.py`, 5 test files | `make_jpeg_bytes`, `make_png_bytes`, `upload_and_crop`, `make_grid`, `client` centralized |
| AC12 | Extract shared brightness utility | Done | `src/rendering/color_utils.py`, `src/rendering/pdf.py`, `src/rendering/preview.py` | `perceived_brightness()` used in 3 locations |
| AC13 | Pin dependency upper bounds | Done | `requirements.txt` | All deps now have upper bounds |
| AC14 | Separate test/runtime deps | Done | `requirements.txt`, `requirements-dev.txt` | pytest/httpx moved to `requirements-dev.txt` |
| AC15 | Remove unused ErrorResponse | Done | `src/api/schemas.py` | Dead code removed |
| AC16 | Fix misleading config comments | Done | `src/config.py` | Comments now note values are defaults |
| AC17 | Drop scipy from requirements | Done | `requirements.txt` | scipy line removed |
| AC18 | Batch LAB conversion in warnings | Done | `src/api/routes.py` | Single `cvtColor` call for all palette colors |

## Files Changed

### Source Files

| File | Change Type | What Changed | Why |
|------|-------------|--------------|-----|
| `src/api/routes.py` | Modified | Validation in `_get_image_dir`; try/except in `_load_image`; KeyError catch in `_run_pipeline`; uint8 dtype in palette edit; batched LAB conversion | AC1, AC2, AC3, AC6, AC18 |
| `src/api/schemas.py` | Modified | Added `PaletteEntry` model; updated `ProcessResponse`/`PaletteEditResponse`; removed `ErrorResponse` | AC10, AC15 |
| `src/config.py` | Modified | `_parse_int_env` helper; `validate_config()`; fixed comments | AC7, AC16 |
| `src/main.py` | Modified | Added CORS, CSP middlewares; called `validate_config()` at startup | AC8, AC9, AC7 |
| `src/processing/grid.py` | Modified | Replaced `scipy.stats.mode` with `np.bincount().argmax()` | AC4 |
| `src/processing/quantization.py` | Modified | Added `.round()` before uint8 cast | AC5 |
| `src/rendering/color_utils.py` | Created | Shared `perceived_brightness()` function | AC12 |
| `src/rendering/pdf.py` | Modified | Uses `perceived_brightness` from color_utils | AC12 |
| `src/rendering/preview.py` | Modified | Uses `perceived_brightness` from color_utils | AC12 |
| `requirements.txt` | Modified | Upper bounds added; scipy removed; test deps removed | AC4, AC13, AC14 |
| `requirements-dev.txt` | Created | Test-only dependencies | AC14 |

### Test Files

| File | Change Type | What Changed | Covers |
|------|-------------|--------------|--------|
| `tests/conftest.py` | Modified | Added shared helpers: `client`, `make_jpeg_bytes`, `make_png_bytes`, `upload_and_crop`, `make_grid` | AC11 |
| `tests/test_audit_fixes.py` | Created | 18 new tests for all audit ACs | AC1–AC14 |
| `tests/test_integration.py` | Modified | Uses shared helpers from conftest | AC11 |
| `tests/test_mosaic_modes_integration.py` | Modified | Uses shared helpers from conftest | AC11 |
| `tests/test_palette_edit_integration.py` | Modified | Uses shared helpers from conftest | AC11 |
| `tests/test_mosaic_modes.py` | Modified | Uses shared `make_grid` from conftest | AC11 |
| `tests/test_preview.py` | Modified | Uses shared `make_grid` from conftest | AC11 |
| `tests/test_palette_edit.py` | Modified | Uses uint8 dtype (was float64) | AC6 |

## Test Results
- **Baseline**: 81 passed, 0 failed (before implementation)
- **Final**: 99 passed, 0 failed (after implementation)
- **New tests added**: 18
- **Regressions**: None

## Deviations from Plan
- **Batched LAB conversion**: The audit recommended per-color `cv2.cvtColor` optimization as a low-priority performance item. Combined it with AC6 dtype fix since both touch the same `_compute_palette_warnings` function.
- **CORS origin configuration**: Made the allowed origin configurable via `CORS_ALLOWED_ORIGINS` env var rather than hardcoding, for deployment flexibility.

## Gaps
None — all 18 priority items from the audit report were implemented.

## Reviewer Focus Areas
- Path traversal validation in `src/api/routes.py:_get_image_dir` — verify the regex matches the existing `_validate_id` pattern
- `_compute_palette_warnings` dtype handling — ensure `np.asarray(..., dtype=np.uint8)` doesn't mask edge cases with existing palettes
- CSP header policy in `src/main.py` — verify the allowed sources match the actual CDN usage in `static/index.html`
- `validate_config()` called in lifespan — confirm it doesn't break test client startup
- scipy removal in grid.py — `np.bincount(region.flat).argmax()` assumes region contains non-negative integers
