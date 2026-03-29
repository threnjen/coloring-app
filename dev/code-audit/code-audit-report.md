# Coloring App — Code Audit Report

**Date:** 2026-03-28
**Scope:** Full codebase — all application source, dependency manifests, and test files
**Auditor:** Code Auditor (automated)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Source files audited** | 18 |
| **Dependency manifests audited** | 3 |
| **Test files audited (reduced lens)** | 16 |
| **Critical findings** | 0 |
| **High findings** | 2 |
| **Medium findings** | 14 |
| **Low findings** | 11 |
| **Total findings** | 27 |

---

## Findings by Category

### 1. Cleanup & Condensing

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 1.1 | `src/config.py` | L20 | Medium | Unused constant | `ALLOWED_MIME_TYPES` is defined but never imported or referenced in any source file. Upload validation uses magic bytes instead. |
| 1.2 | `src/config.py` | L35 | Low | Vestigial constant | `COMPONENT_SIZE_MM` is only used to compute `PRINTABLE_*` and `MARGIN_*` values that are themselves unused in application code (only in tests). |
| 1.3 | `src/config.py` | L56–62 | Low | Vestigial constants | `PRINTABLE_WIDTH_MM`, `PRINTABLE_HEIGHT_MM`, `MARGIN_SIDE_MM`, `MARGIN_TOP_MM` are unused in application code. `pdf.py` re-computes margins dynamically from `PAPER_WIDTH_MM` and `PAPER_HEIGHT_MM`. Only referenced in `tests/test_pdf.py`. |
| 1.4 | `src/api/schemas.py` | L128–137 | Medium | Dead code | `CompositeRequest` Pydantic model is defined but never imported or used anywhere. The `composite_image` endpoint manually parses the request instead. |
| 1.5 | `src/api/routes.py` | L442 | Low | Redundant computation | In `_compute_palette_warnings`, `other_rgb` is reconstructed from `palette.colors_rgb[i]` inside the LAB similarity loop, but `all_rgb[i]` is already available and equivalent. |

### 2. Errors & Defects

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 2.1 | `src/api/routes.py` | L489–500 | High | Race condition | `edit_palette` mutates `palette.colors_rgb` in the event loop, then calls `asyncio.to_thread(_render_and_save)` which reads the palette. A concurrent palette edit between the mutation and the render completion could produce an inconsistent preview. |
| 2.2 | `src/rendering/pdf.py` | L125–147, L149–171 | Medium | Unused parameter | `palette` parameter in `_draw_circle_cell` and `_draw_hexagon_cell` is accepted but never referenced in the method body. Likely a copy-paste artifact. |
| 2.3 | `src/api/routes.py` | L258–263 | Medium | Missing exception chain | `except KeyError: raise HTTPException(...)` lacks a `from` clause. The original `KeyError` traceback is lost. Should be `raise HTTPException(...) from exc`. |

### 3. Type Hints

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 3.1 | `src/api/routes.py` | L575 | Medium | Missing return type | `composite_image` has no return type annotation. All other endpoints declare `-> Response` or `-> <ResponseModel>`. |
| 3.2 | `src/models/mosaic.py` | L85 | Medium | Overly broad type | `mode: str = "square"` should be constrained (e.g., `Literal["square", "circle", "hexagon"]` or reuse `MosaicMode` enum) to prevent invalid values at construction time. |
| 3.3 | `src/rendering/pdf.py` | L125, L149 | Low | Unnecessary forward reference | `palette: "ColorPalette"` uses a string annotation, but `ColorPalette` is already imported at the top of the file. Should be `palette: ColorPalette`. |
| 3.4 | `src/processing/backgrounds.py` | L35 | Low | Untyped structure | `_PROGRAMMATIC_BACKGROUNDS: list[dict]` — the `dict` is untyped. A `TypedDict` or dataclass would make the expected shape explicit. |

### 4. Documentation

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 4.1 | `src/config.py` | L35–62 | Low | Misleading constants | `COMPONENT_SIZE_MM`, `PRINTABLE_*`, `MARGIN_*` appear authoritative but are only valid for the default 3mm/square case. No comment indicates they are vestigial or test-only. |

### 5. Readability, Brevity & Clarity

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 5.1 | `src/api/routes.py` | L575–700 | Medium | Long complex function | `composite_image` is ~125 lines with branching for JSON vs multipart, nested try/except, and manual parameter extraction. Could be decomposed into `_parse_composite_json` and `_parse_composite_form` helpers. |
| 5.2 | `src/api/routes.py` | whole file | Medium | Large module | At ~700 lines with 11 endpoints + helpers, this module handles upload, crop, process, preview, PDF, palette edit, cutout, backgrounds, and composite. Consider splitting into feature-specific route modules. |

### 6. Security Posture

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 6.1 | `src/api/routes.py` | L575–632 | Medium | Validation bypass | `composite_image` manually parses `request.json()` / `request.form()` instead of using Pydantic models. `CompositeRequest.scale` bounds (0.25–2.0) are not validated at the API layer — only clamped silently inside `Compositor.composite()`. Malformed requests may not receive proper 422 validation errors. |

**Positive observations:** UUID hex validation, magic-byte validation, CSP headers, explicit CORS restrictions, file size limits, path traversal defense-in-depth are all solid.

### 7. Library & Dependency Simplicity

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 7.1 | `requirements.txt` | L5 | Low | Heavy dependency | `scikit-learn` is pulled in solely for `KMeans` in `quantization.py`. The rest of the library (~50MB installed) is unused. OpenCV's `cv2.kmeans` could replace it with no additional dependency. |

### 8. Consistency

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 8.1 | `src/rendering/pdf.py` | L97–171 | Medium | Inconsistent method signatures | `_draw_square_cell` takes 7 params (no `palette`), while `_draw_circle_cell` and `_draw_hexagon_cell` take 8 (including `palette` which they don't use). All three should have a consistent signature. |
| 8.2 | `src/api/routes.py` | L575 | Low | Inconsistent request parsing | All other endpoints use Pydantic request models (`CropRequest`, `ProcessRequest`, etc.), but `composite_image` manually parses `Request`. Breaks the established pattern. |

### 9. DRY & Deduplication

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 9.1 | `src/processing/backgrounds.py` | L63, L84 | Medium | Repeated filesystem scan | `_scan_presets()` is called in both `list_backgrounds()` and `get_background()`, re-scanning the preset directory on every API request. |
| 9.2 | `tests/test_cutout.py` / `tests/test_image_editing_integration.py` | — | Low | Duplicated mock (test) | `_mock_rembg_remove` is implemented in both test files with slightly different logic. Should be shared via conftest. |
| 9.3 | `tests/test_pdf.py` / `tests/test_mosaic_modes.py` / `tests/test_palette_edit.py` | — | Low | Duplicated helper (test) | `_make_sheet` helper is defined independently in 3 test files with slightly different signatures. Could be consolidated into conftest. |
| 9.4 | `tests/test_image_editing_integration.py` | L13–15 | Low | Redundant fixture (test) | `client` fixture is redefined identically to the one already in `conftest.py`. |

### 10. Error Handling Patterns

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 10.1 | `src/api/routes.py` | L258–263 | Medium | Lost exception context | `except KeyError: raise HTTPException(...)` — original `KeyError` is discarded without `from exc`. Use `raise ... from exc` to preserve context. (Cross-ref with 2.3.) |
| 10.2 | `src/api/routes.py` | L618 | Low | Overly broad except | `except Exception as exc` for JSON parsing. `json.JSONDecodeError` (or `ValueError`) would be more precise and avoid masking unexpected errors. |

### 11. Configuration Hygiene

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 11.1 | `src/config.py` | L20 | Medium | Orphaned config | `ALLOWED_MIME_TYPES` suggests MIME-type validation exists, but it's never used. Either integrate into upload validation or remove to avoid confusion. (Cross-ref with 1.1.) |
| 11.2 | `src/config.py` | L35–62 | Low | Stale defaults | `COMPONENT_SIZE_MM`, `PRINTABLE_*`, `MARGIN_*` are holdovers from the single-size era. With multi-size support via `GRID_DIMENSIONS`, these config values are misleading. (Cross-ref with 1.2, 1.3, 4.1.) |

### 12. Logging Quality

No significant findings. Logging is consistent, appropriately leveled, includes timing and IDs, and avoids sensitive data. Well done.

### 13. Performance Anti-Patterns

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 13.1 | `src/processing/backgrounds.py` | L63, L84 | Medium | Repeated I/O | `_scan_presets()` does a filesystem `iterdir()` on every API call. Presets are static files — results should be cached (scan once at startup or on first call). (Cross-ref with 9.1.) |
| 13.2 | `src/rendering/preview.py` | L64–77 | Low | Font loaded per render | Font discovery (`ImageFont.truetype(...)` with fallback chain) runs on every `render()` call. Could be loaded once at module or instance level. |

### 14. API Contract Adherence

| # | File | Line(s) | Severity | Finding | Detail |
|---|------|---------|----------|---------|--------|
| 14.1 | `src/api/routes.py` | L575–700 | High | Schema bypass | `composite_image` accepts raw `Request` and manually extracts fields instead of using `CompositeRequest` schema. This means: (a) `scale` bounds (0.25–2.0) are not validated at the API layer, (b) missing fields produce ad-hoc 400 errors instead of standard 422 validation errors, (c) the defined `CompositeRequest` in `schemas.py` is dead code, (d) OpenAPI docs/schema are inaccurate for this endpoint. |

---

## Cross-Cutting Observations

### Pydantic usage inconsistency
All endpoints except `composite_image` use Pydantic request models. The composite endpoint's manual parsing breaks the pattern and introduces validation gaps. The `CompositeRequest` schema already exists but is never wired up.

### Test helper duplication
`_make_sheet` and `_mock_rembg_remove` are independently defined across multiple test files. Centralizing these in `conftest.py` would reduce duplication and ensure consistent test setup.

### Vestigial config constants
Several config values (`ALLOWED_MIME_TYPES`, `COMPONENT_SIZE_MM`, `PRINTABLE_*`, `MARGIN_*`) appear to be remnants from earlier development phases. They are either unused entirely or only referenced in tests that could compute values directly.

### PDF renderer method signatures
The three cell-drawing methods (`_draw_square_cell`, `_draw_circle_cell`, `_draw_hexagon_cell`) have inconsistent signatures. The latter two accept `palette` but don't use it.

---

## Recommended Priority Order

### 1. Quick wins (low effort, high impact)
- Remove unused `palette` param from `_draw_circle_cell`/`_draw_hexagon_cell` in `pdf.py` (or add to `_draw_square_cell` if future use is planned)
- Add `from exc` to the `except KeyError` in `_run_pipeline` (routes.py L258–263)
- Add return type annotation to `composite_image`
- Remove or comment out `ALLOWED_MIME_TYPES` from config.py
- Remove forward-reference quotes from `"ColorPalette"` in pdf.py

### 2. Important fixes (correctness & security)
- Refactor `composite_image` to use `CompositeRequest` Pydantic model for JSON requests (keep multipart as manual or use FastAPI's `Form` + `File` pattern) — resolves findings 14.1, 6.1, 8.2, 1.4
- Add a copy/lock mechanism in `edit_palette` to prevent race conditions on concurrent edits

### 3. Improvement pass (structure & DRY)
- Cache `_scan_presets()` results (scan once at startup or on first call)
- Consolidate test helpers (`_make_sheet`, `_mock_rembg_remove`) into `conftest.py`
- Add `Literal` or enum constraint to `MosaicSheet.mode`
- Type `_PROGRAMMATIC_BACKGROUNDS` more precisely with `TypedDict`
- Clean up vestigial config constants (`COMPONENT_SIZE_MM`, `PRINTABLE_*`, `MARGIN_*`)

### 4. Polish (scalability & architecture)
- Split `routes.py` into feature-specific route modules (e.g., `routes_upload.py`, `routes_mosaic.py`, `routes_editing.py`)
- Cache font loading in `PreviewRenderer`
- Evaluate replacing `scikit-learn` with `cv2.kmeans` to reduce dependency weight (~50MB savings)
- Narrow `except Exception` to `json.JSONDecodeError` in composite endpoint
