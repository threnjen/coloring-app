# Code Audit Summary — coloring-app

**Date:** 2026-03-27
**Full report:** `dev/active/code-audit/code-audit-report.md`

---

## Overview

| Metric | Value |
|--------|-------|
| Files audited | 22 |
| Critical findings | 1 |
| High findings | 5 |
| Medium findings | 18 |
| Low findings | 12 |
| **Total** | **36** |

---

## Critical & High Findings

| # | Severity | Category | File(s) | Summary |
|---|----------|----------|---------|---------|
| 1 | **Critical** | Security / Defects | `src/api/routes.py` L117-122 | **Path traversal**: `_get_image_dir` builds filesystem paths from `image_id` without internal validation. Defense in depth requires co-locating the hex-UUID check with the path construction. |
| 2 | **High** | Consistency | `src/processing/quantization.py`, `src/api/routes.py`, `tests/test_palette_edit.py` | **dtype mismatch**: `ColorPalette.colors_rgb` is `uint8` from quantization but `float64` from palette editing. Causes unreliable `np.array_equal` comparisons in duplicate-color warnings. |
| 3 | **High** | Security | `src/api/routes.py` | **No CORS middleware**: App has no explicit CORS configuration. Safe as same-origin default, but risky if cross-origin access is ever needed. |
| 4 | **High** | Configuration | `src/config.py` L8-10 | **No env var validation**: `int(os.getenv(...))` at import time crashes with unhelpful error on non-numeric values. |
| 5 | **High** | Configuration | `src/config.py` | **No centralized config**: Env vars scattered as module-level constants without validation or typing. |

---

## Priority Action Items

### Immediate (Critical + Quick Wins)
1. **Path traversal fix** — Add hex-UUID validation inside `_get_image_dir`
2. **Corrupt image handling** — Wrap `Image.open()` in try/except in `_load_image`
3. **KeyError guard** — Catch missing `GRID_DIMENSIONS` key in `_run_pipeline`
4. **Drop scipy** — Replace `scipy.stats.mode` with `np.bincount().argmax()`
5. **Fix quantization precision** — Use `.round().astype(np.uint8)` for LAB center conversion

### Short-term (High severity)
6. **Standardize dtype** — Pick `float64` or `uint8` for `colors_rgb` everywhere
7. **Env var validation** — Add startup checks or adopt pydantic-settings
8. **Add CORS** — Configure `CORSMiddleware` with explicit origins
9. **Add CSP header** — Restrict script/style sources

### Medium-term (DRY, types, contracts)
10. Define `PaletteEntry` model for typed API responses
11. Centralize test helpers in `conftest.py`
12. Extract shared brightness utility
13. Pin dependency upper bounds
14. Separate test from runtime dependencies

### Low priority (Polish)
15. Extract JS palette-building logic
16. Break up `_draw_grid_page`
17. Remove unused `ErrorResponse`
18. Clean up magic numbers and misleading comments
