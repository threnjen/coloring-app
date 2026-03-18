# Mosaic Coloring App — Master Plan

## Overview

A web application that converts uploaded photos into mosaic color-by-number coloring sheets. Five phases, from core pipeline POC through print-on-demand book ordering.

Full phase details: `docs/phases/PHASE_N_*.md`

---

## 1. Requirements & Traceability

### Acceptance Criteria

| ID | Criterion | Phase |
|----|-----------|-------|
| AC1 | User uploads a photo (JPEG, PNG) via web interface | 1 |
| AC2 | User zooms/crops to select a region | 1 |
| AC3 | App enhances contrast and saturation | 1 |
| AC4 | User selects 8–20 colors; app quantizes via K-means in LAB | 1 |
| AC5 | App generates square pixel grid with single-character labels | 1 |
| AC6 | App generates circle grid with black inter-cell space | 2 |
| AC7 | User selects component size: 4mm, 5mm, or 6mm | 2 |
| AC8 | User sees on-screen preview | 1 |
| AC9 | User manually edits colors; preview updates | 2 |
| AC10 | Cutout tool extracts subject via background removal | 3 |
| AC11 | Paste cutout onto preset or custom backgrounds | 3 |
| AC12 | Download PDF: grid page + legend page (US Letter) | 1 |
| AC13 | Email PDF as attachment | 4 |
| AC14 | Save/manage multiple sheets in a session | 4 |
| AC15 | Order spiral-bound book via Lulu (20+ sheets) | 5 |

### Non-Goals

- Mobile native app (web only)
- User accounts / authentication
- Paper sizes other than US Letter
- Real-time collaboration
- E-commerce beyond Lulu

### Traceability Matrix

| AC | Code Areas | Planned Tests |
|----|-----------|---------------|
| AC1 | `src/api/routes.py`, `static/js/app.js` | Unit: file validation; Integration: upload round-trip |
| AC2 | `static/js/crop.js`, `src/api/routes.py` | Integration: crop coordinates → cropped image |
| AC3 | `src/processing/enhancement.py` | Unit: contrast/saturation increase |
| AC4 | `src/processing/quantization.py` | Unit: correct color count, LAB space |
| AC5 | `src/processing/grid.py` | Unit: grid dimensions, label assignment |
| AC6 | `src/rendering/grid_circle.py` | Unit: circle rendering, black gaps |
| AC7 | `src/config.py`, `src/api/schemas.py` | Unit: dimension lookup per size |
| AC8 | `src/rendering/preview.py`, `static/js/app.js` | Integration: preview image renders |
| AC9 | `src/api/routes.py`, `static/js/app.js` | Unit: color swap updates grid; Integration: round-trip |
| AC10 | `src/processing/cutout.py` | Unit: RGBA output, smooth mask |
| AC11 | `src/processing/compositing.py` | Unit: composite dimensions, positioning |
| AC12 | `src/rendering/pdf.py` | Unit: 2-page PDF, correct dimensions |
| AC13 | `src/email/sender.py` | Unit: validation, rate limit; Integration: send (mocked) |
| AC14 | `src/persistence/storage.py` | Unit: CRUD; Integration: save/load round-trip |
| AC15 | `src/book/assembly.py`, `src/book/lulu.py` | Unit: page count/order; Integration: Lulu flow (mocked) |

---

## 2. Correctness & Edge Cases

### Key Workflows and Failure Modes

| Workflow | Failure Mode | Mitigation |
|----------|-------------|------------|
| Image upload | Non-image file, oversized file | Validate magic bytes + size limit (20MB) |
| Crop | Region too small (< 50px) | Reject with descriptive error |
| Enhancement | Monochrome image | Boost what's there; warn if few distinct colors result |
| Quantization | Requested colors > distinct colors in image | Return actual count; UI reflects it |
| Grid rendering | 2-digit labels overflow cells | Single-character scheme (0–9, A–J) eliminates this |
| Circle rendering | Label illegible in small circles | Font size tested at 4mm minimum |
| PDF generation | 3,250 cells at 4mm | Benchmark rendering time; optimize if >5s |
| Cutout | No clear foreground | Show mask preview; user can revert |
| Email | Invalid address, rate abuse | Format validation + 5/hr rate limit |
| Persistence | Session lost (cookie cleared) | Accept for now; no auth in scope |
| Book assembly | Odd page count | Pad with blank page |
| Lulu API | Downtime, API changes | Graceful errors; isolate Lulu code |

### Validation Rules

- Upload: JPEG/PNG only (magic bytes), max 20MB
- Crop: minimum 50×50 pixels
- Color count: integer, 8–20 inclusive
- Component size: enum {4, 5, 6} mm
- Mosaic mode: enum {square, circle}
- Email: RFC-compliant format
- Sheet title: max 100 characters, HTML stripped
- Book: minimum 20 sheets selected

### Error Handling Strategy

- **400 errors**: Invalid input (bad format, out of range) — descriptive message to user
- **500 errors**: Processing failures — log full traceback, return generic "processing failed" to user, clean up temp files
- All errors logged via Python `logging` module; never `print()`

---

## 3. Consistency & Architecture Fit

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12+ / FastAPI |
| Frontend | Vanilla HTML/JS/CSS + Cropper.js |
| Image Processing | Pillow, OpenCV, scikit-learn |
| Background Removal | rembg (Phase 3) |
| PDF | ReportLab |
| Persistence | SQLite (Phase 4+) |
| Email | Resend / Postmark / SendGrid (Phase 4) |
| Print-on-Demand | Lulu API (Phase 5) |

### Conventions (per STYLE_GUIDE.md)

- OOP preferred; classes over standalone functions
- `logging` module, no `print()`
- Config in `config.py`; no magic strings
- `lower_with_under` for modules/functions; `CapWords` for classes; `CAPS_WITH_UNDER` for constants
- Type annotations on public APIs
- Specific exception handling; custom exceptions end with `Error`
- Stdlib imports → third-party → local; one per line

### Proposed Deviations

None. The stack and patterns align with existing project conventions.

---

## 4. Clean Design & Maintainability

### Simplest Design Principles

- Grid is the core data structure — a 2D array of cells with `(row, col, color_index, label)`
- All rendering (preview, PDF, book) reads from the same grid structure
- Processing pipeline is a linear chain: upload → crop → [edit] → enhance → quantize → grid → render
- Each step is a pure function (input image/data → output image/data) — easy to test
- Frontend is a simple step-by-step wizard, not a complex SPA

### Complexity Risks

| Risk | Mitigation |
|------|------------|
| Image processing performance on large images | Resize before processing; benchmark early in Phase 1 |
| Circle rendering math | Isolate in its own module; extensive unit tests |
| Lulu API coupling | Adapter pattern — isolate all Lulu specifics behind an interface |
| Frontend state management | Keep it simple: one global state object, sequential wizard steps |

### Keep-It-Clean Checklist

- [ ] Each processing step is a separate module with a single public function/class
- [ ] No module exceeds ~200 lines
- [ ] Grid data structure shared across all rendering modes
- [ ] Config values in `config.py`, never hardcoded
- [ ] Test fixtures are small, representative images (not large photos)

---

## 5. Completeness: Observability, Security, Operability

### Logging & Metrics

- Log every pipeline step with timing (upload, crop, enhance, quantize, grid, render)
- Log image metadata: dimensions, file size, format
- Log all external API calls (Lulu, email provider): endpoint, status, latency
- Log session/sheet lifecycle events
- Structured logging (JSON format) for future log aggregation

### Security

- Validate all uploads (magic bytes, size, format)
- Sanitize all user text input (titles, email addresses)
- Use parameterized queries for SQLite
- Store API keys as environment variables
- HttpOnly, SameSite cookies for sessions
- No user input in file paths or shell commands
- Rate limit email sending

### Operability

- **Run locally**: `pip install -r requirements.txt && python -m src.main`
- **Config**: All settings via environment variables with sensible defaults
- **Temp cleanup**: Configurable TTL for temp files; cleanup on startup
- **Rollback**: Each phase is independently deployable; no irreversible migrations

---

## 6. Test Plan

### Test Strategy by Phase

| Phase | Unit | Integration | Visual Regression | Manual QA |
|-------|------|------------|-------------------|-----------|
| 1 | Enhancement, quantization, grid, PDF | Full pipeline | Grid golden refs | 8 scenarios |
| 2 | Circle grid, CLAHE, palette edit | Mode switching, size change | Circle golden refs | 7 scenarios |
| 3 | Cutout, compositing | Cutout-to-PDF pipeline | Composite golden refs | 8 scenarios |
| 4 | Persistence CRUD, email | Save/load round-trip | N/A | 8 scenarios |
| 5 | Book assembly, page ordering | Lulu flow (mocked) | N/A | 8 scenarios |

### Test Data & Fixtures

- 3–4 small test images (< 500KB each): landscape, portrait, low-contrast, transparent PNG
- Golden reference grid images generated with fixed random seed (deterministic K-means)
- Mocked Lulu API responses (JSON fixtures)
- Mocked email provider responses

### Top 5 Cross-Cutting Test Cases

1. **Full pipeline**: Upload landscape → crop → enhance → 12 colors → 4mm square → PDF has 2 pages with correct grid dimensions and legend.

2. **Mode preservation through save/load**: Process as circle at 5mm with palette edits → save → load → all state restored exactly.

3. **Cutout compositing pipeline**: Upload portrait → crop → cutout subject → white background → process → mosaic shows clean subject without background noise.

4. **Book assembly page ordering**: 22 sheets → assemble → PDF has 45 pages → page 1 is title → pages alternate legend/grid correctly.

5. **Error resilience**: Upload .txt file → 400 error. Crop 10px region → descriptive error. Request 25 colors → rejected. Each error logged with context.

---

## Stages Summary

| Stage | Name | Goal | Status |
|-------|------|------|--------|
| 1 | Core Pipeline POC | End-to-end: upload → crop → enhance → quantize → square grid → preview → PDF | Not Started |
| 2 | Mosaic Modes & Color Refinement | Circle mode, size selector, advanced enhancement, palette editing | Not Started |
| 3 | Image Editing Tools | Subject cutout, background compositing | Not Started |
| 4 | Export, Sharing & Persistence | Email PDF, save/load, multi-sheet management | Not Started |
| 5 | Print-on-Demand | Lulu API, book assembly, ordering | Not Started |
