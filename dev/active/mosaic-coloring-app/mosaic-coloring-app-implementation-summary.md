# Phase 1 Implementation Summary

## Acceptance Criteria → Outcomes

```
AC1: User can upload a photo (JPEG, PNG) via web interface
  → Done. POST /api/upload validates magic bytes, size, stores as PNG. Frontend file picker in index.html.

AC2: User can zoom and crop to select a rectangular region
  → Done. POST /api/crop validates bounds/min size. Frontend uses Cropper.js (crop.js).

AC3: App applies basic contrast and saturation enhancement
  → Done. ImageEnhancer in processing/enhancement.py boosts contrast in LAB + saturation in HSV.

AC4: User selects number of colors (8–20 via slider)
  → Done. Range slider in index.html, validated by Pydantic schema (ProcessRequest).

AC5: App quantizes using K-means in CIELAB color space
  → Done. ColorQuantizer in processing/quantization.py uses sklearn KMeans on LAB pixels.

AC6: App generates square pixel grid at 4mm (50×65)
  → Done. GridGenerator in processing/grid.py downsamples label map to 50×65 cells via mode.

AC7: Each cell displays single-character label (0–9, A–J)
  → Done. LABEL_CHARS in config.py; ColorPalette.label() maps indices to chars.

AC8: User sees on-screen preview of the generated mosaic grid
  → Done. PreviewRenderer in rendering/preview.py generates colored PNG; served via GET /api/preview/{id}.

AC9: User can download a PDF: grid page + legend page
  → Done. PdfRenderer in rendering/pdf.py; served via GET /api/pdf/{id} with Content-Disposition header.

AC10: PDF grid fills printable area (200mm × 263.5mm) on US Letter
  → Done. Grid layout uses MARGIN_SIDE_MM/MARGIN_TOP_MM from config.py; cells at 4mm = 200mm × 260mm.
```

## Files Changed / Added

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, pytest/ruff config |
| `requirements.txt` | Phase 1 Python dependencies |
| `src/__init__.py` | Package init |
| `src/config.py` | All configurable constants |
| `src/main.py` | FastAPI app entry point, lifespan, static files |
| `src/api/__init__.py` | Package init |
| `src/api/schemas.py` | Pydantic request/response models |
| `src/api/routes.py` | All API endpoints: upload, crop, process, preview, PDF |
| `src/processing/__init__.py` | Package init |
| `src/processing/enhancement.py` | Contrast + saturation enhancement |
| `src/processing/quantization.py` | K-means color quantization in LAB |
| `src/processing/grid.py` | Grid generation (label map → GridCell 2D array) |
| `src/rendering/__init__.py` | Package init |
| `src/rendering/preview.py` | Preview PNG rendering |
| `src/rendering/pdf.py` | PDF generation (grid + legend pages) |
| `src/models/__init__.py` | Package init |
| `src/models/mosaic.py` | Data classes: ColorPalette, GridCell, MosaicSheet |
| `static/index.html` | Single-page UI with 4 wizard steps |
| `static/css/style.css` | App styles |
| `static/js/app.js` | Main frontend logic, API integration |
| `static/js/crop.js` | Cropper.js wrapper |
| `tests/__init__.py` | Package init |
| `tests/conftest.py` | Shared test fixtures |
| `tests/test_enhancement.py` | 4 tests for enhancement (AC3) |
| `tests/test_quantization.py` | 5 tests for quantization (AC5) |
| `tests/test_grid.py` | 5 tests for grid generation (AC6, AC7) |
| `tests/test_pdf.py` | 4 tests for PDF generation (AC9, AC10) |
| `tests/test_integration.py` | 12 tests: upload, crop, full pipeline (AC1–AC10) |

## Review-Critical Checklist

- [x] Plan ↔ code traceability complete (all 10 ACs mapped)
- [x] Consistent patterns followed (OOP, logging, config, naming per STYLE_GUIDE.md)
- [x] Cleanliness and readability (small focused classes, clear data flow)
- [x] Edge cases and error handling covered (transparent PNG, oversized files, small crops, missing images)
- [x] Observability and tests complete (30 tests passing, timing logs in pipeline)

## Deviations from Plan

- `PRINTABLE_HEIGHT_MM` in config is 263.5mm per plan spec, but actual grid height at 4mm×65 rows = 260mm. This is consistent with the plan's grid specification (65 rows × 4mm). The 3.5mm gap is used as extra bottom margin.
- `scipy.stats.mode` used for grid cell assignment (majority vote) rather than a simpler approach — this ensures the most representative color wins per cell region.

## Known Limitations (Phase 1)

- **PDF unavailable after server restart.** Mosaic sheet data (grid, palette) lives only in process memory (`_mosaic_store`). A server restart loses all mosaic data. Users who still have the preview page open will get 404 on PDF download. This is an accepted Phase 1 limitation — Phase 4 (Persistence) will add durable storage.

## Gaps or Blockers

None. All Phase 1 acceptance criteria are implemented and tested. The app can be started with:

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload
```

## Test Results

```
30 passed, 6 warnings in 42.97s
```

Warnings are expected sklearn ConvergenceWarnings when test images have fewer distinct colors than requested clusters — the code handles this gracefully (logs a warning, returns actual count).
