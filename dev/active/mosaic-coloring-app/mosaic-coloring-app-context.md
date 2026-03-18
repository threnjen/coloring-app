# Mosaic Coloring App — Context

## Key Files to Create

### Phase 1

| File | Purpose |
|------|---------|
| `src/main.py` | FastAPI app entry point; serves static files + mounts API router |
| `src/config.py` | All constants: grid sizes, margins, color range, upload limits, paths |
| `src/api/routes.py` | API endpoints: upload, crop, process, preview, PDF download |
| `src/api/schemas.py` | Pydantic models for all request/response payloads |
| `src/processing/enhancement.py` | Contrast and saturation enhancement (basic: Phase 1, advanced: Phase 2) |
| `src/processing/quantization.py` | K-means color quantization in CIELAB space |
| `src/processing/grid.py` | Grid generation: image → 2D array of GridCell objects |
| `src/rendering/preview.py` | Generate preview PNG from grid data |
| `src/rendering/pdf.py` | ReportLab PDF: grid page + legend page |
| `src/models/mosaic.py` | Data classes: `ColorPalette`, `GridCell`, `MosaicSheet`, `Label` |
| `static/index.html` | Single-page UI: upload, crop, process, preview, download |
| `static/css/style.css` | App styles |
| `static/js/app.js` | Main frontend logic, API calls, state management |
| `static/js/crop.js` | Cropper.js integration for zoom/crop |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Project metadata, tool config |
| `tests/` | Test directory with fixtures and golden references |

### Phase 2 Additions

| File | Purpose |
|------|---------|
| `src/rendering/grid_circle.py` | Circle mosaic rendering |
| `src/rendering/grid_square.py` | Renamed from grid rendering in `preview.py` |

### Phase 3 Additions

| File | Purpose |
|------|---------|
| `src/processing/cutout.py` | Background removal via `rembg` |
| `src/processing/compositing.py` | Subject + background compositing |
| `static/presets/` | Preset background images |
| `static/js/editor.js` | Image editing UI (cutout, backgrounds, position/scale) |

### Phase 4 Additions

| File | Purpose |
|------|---------|
| `src/persistence/storage.py` | SQLite session + sheet storage |
| `src/persistence/models.py` | Database models |
| `src/email/sender.py` | Transactional email sending |

### Phase 5 Additions

| File | Purpose |
|------|---------|
| `src/book/assembly.py` | Book PDF assembly |
| `src/book/cover.py` | Cover page generation |
| `src/book/lulu.py` | Lulu API client |
| `src/book/specs.py` | Lulu print specifications |
| `static/js/book.js` | Book builder UI |

## Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| Python + FastAPI | Best image processing ecosystem (Pillow, OpenCV, scikit-learn); FastAPI serves both API and static files |
| Vanilla HTML/JS frontend | No build step; simplest possible for POC; Cropper.js for crop interaction |
| K-means in CIELAB color space | Perceptually uniform — similar distances = similar perceived colors; avoids RGB clustering issues |
| Single-character labels (0–9, A–J) | Fits in 4mm cells; covers 8–20 color range; matches reference coloring book |
| 50 columns at 4mm = ground truth | Derived from physical reference book; margins (~8mm/side) follow from this |
| ReportLab for PDF | Precise layout control needed for grid cells at exact mm dimensions; mature Python library |
| `rembg` for background removal | Runs locally (no API key); U2-Net model is well-tested for subject extraction |
| SQLite for persistence | Zero-config; single file; sufficient for single-user/small-scale; no external database needed |
| Legend on separate page | Maximizes grid area; matches reference book layout |
| Lulu for print-on-demand | Has an API; supports spiral-bound color books on US Letter |

## Constraints

| Constraint | Detail |
|-----------|--------|
| Paper size | US Letter only (215.9mm × 279.4mm) |
| Grid ground truth | 50 columns × 4mm = 200mm printable width; ~8mm side margins |
| Color range | 8–20 colors |
| Component sizes | 4mm, 5mm, 6mm |
| Label scheme | 0–9 then A–J (single character per cell) |
| No auth | Anonymous sessions via cookie; no user accounts |
| Local-first | Must run locally with `pip install` + `python` — no Docker/cloud required for POC |

## Grid Dimension Reference

| Size | Columns | Rows | Cells | Printable Width | Printable Height |
|------|---------|------|-------|----------------|-----------------|
| 4mm | 50 | 65 | 3,250 | 200mm | 260mm |
| 5mm | 40 | 52 | 2,080 | 200mm | 260mm |
| 6mm | 33 | 43 | 1,419 | 198mm | 258mm |

Note: 6mm doesn't divide evenly into 200mm (33×6=198mm) — 1mm extra margin on each side. Same for height. This is acceptable.

## Dependencies (Python)

| Package | Version | Purpose | Phase |
|---------|---------|---------|-------|
| fastapi | latest | Web framework | 1 |
| uvicorn | latest | ASGI server | 1 |
| Pillow | latest | Image loading, basic manipulation | 1 |
| opencv-python-headless | latest | Image processing (CLAHE, bilateral filter) | 1–2 |
| scikit-learn | latest | K-means clustering | 1 |
| numpy | latest | Array operations | 1 |
| reportlab | latest | PDF generation | 1 |
| python-multipart | latest | File upload handling in FastAPI | 1 |
| rembg | latest | Background removal | 3 |
| aiosqlite | latest | Async SQLite for persistence | 4 |
| httpx | latest | HTTP client for Lulu API | 5 |

## Open Questions

| # | Question | Status |
|---|----------|--------|
| 1 | Exact Lulu product ID for spiral-bound US Letter color book | Deferred to Phase 5 research |
| 2 | Which transactional email provider to use (Resend/Postmark/SendGrid) | Deferred to Phase 4; all have free tiers |
| 3 | Whether to include a "color reference image" (the processed photo before grid conversion) alongside the grid in the PDF | Could be useful; decide during Phase 1 testing |
| 4 | Maximum upload dimension before resize (currently proposed 4000px) | Validate during Phase 1 performance testing |

## References

- [AGENTS.md](../../AGENTS.md) — project conventions
- [STYLE_GUIDE.md](../../docs/STYLE_GUIDE.md) — Python style rules
- [PLANNING_WORKFLOW.md](../../docs/PLANNING_WORKFLOW.md) — phase planning process
- [PHASES_OVERVIEW.md](../../docs/phases/PHASES_OVERVIEW.md) — phase table and dependencies
