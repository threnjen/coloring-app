# Code Audit — Executive Summary

**Date:** 2026-03-28
**Scope:** Full coloring-app codebase (18 source files, 3 manifests, 16 test files)

---

## Overall Health: Good

The codebase is well-structured with strong security fundamentals (UUID validation, path traversal defense, CSP, CORS), consistent logging, good test coverage, and clean separation of concerns across processing, rendering, and API layers.

## Findings Overview

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 2 |
| Medium | 14 |
| Low | 11 |

## Priority Action Items

### Immediate (High severity)

1. **`composite_image` bypasses Pydantic schema** — The endpoint manually parses raw `Request` instead of using the already-defined `CompositeRequest` model. This means scale bounds aren't validated, error responses are non-standard, and the OpenAPI schema is inaccurate. The `CompositeRequest` model in `schemas.py` is dead code.

2. **Race condition in `edit_palette`** — Palette is mutated in the event loop, then read asynchronously in a thread for preview rendering. Concurrent palette edits can interleave, producing inconsistent previews.

### Short-term (Medium severity, low effort)

3. **Lost exception context** — `except KeyError` in `_run_pipeline` discards the original traceback. Add `from exc`.

4. **Unused `palette` parameter** — `_draw_circle_cell` and `_draw_hexagon_cell` in `pdf.py` accept a `palette` param that's never used, creating an inconsistent API with `_draw_square_cell`.

5. **Orphaned config** — `ALLOWED_MIME_TYPES` is defined but never referenced. Either wire it into upload validation or remove it.

6. **Repeated filesystem scan** — `_scan_presets()` re-reads the preset directory on every API call. Cache the results.

### Medium-term (structural improvements)

7. **`routes.py` is ~700 lines** — Consider splitting into feature-specific modules.

8. **Test helper duplication** — `_make_sheet` (3 files) and `_mock_rembg_remove` (2 files) should be consolidated into `conftest.py`.

9. **`MosaicSheet.mode` is untyped `str`** — Should use `Literal` or `MosaicMode` enum.

10. **`scikit-learn` for one function** — ~50MB dependency used only for `KMeans`. `cv2.kmeans` is a lighter alternative already available via `opencv-python-headless`.

## Strengths

- Strong input validation (magic bytes, UUID hex, file size limits)
- Defense-in-depth path traversal protection
- Consistent structured logging with timing
- CSP and CORS properly configured
- Good test coverage across all processing modules
- Clean separation: processing / rendering / API layers
- CPU-bound work correctly offloaded via `asyncio.to_thread`
