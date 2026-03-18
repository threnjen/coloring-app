# Mosaic Coloring App — Tasks

Ordered checklist of implementation work items. Each item maps to one or more acceptance criteria and is small enough to implement and verify independently.

---

## Phase 1: Core Pipeline POC

### Project Setup
- [ ] Initialize `pyproject.toml` with project metadata and tool config (AC1–AC12)
- [ ] Create `requirements.txt` with Phase 1 dependencies (AC1–AC12)
- [ ] Create `src/config.py` with grid dimensions, margins, color range, upload limits, label scheme (AC4, AC5, AC7)
- [ ] Create `src/models/mosaic.py` with data classes: `ColorPalette`, `GridCell`, `MosaicSheet` (AC4, AC5)
- [ ] Set up `logging` configuration in `src/main.py` (project convention)

### Image Upload & Crop
- [ ] Create `src/main.py` — FastAPI app serving static files + API router (AC1)
- [ ] Create `src/api/schemas.py` — Pydantic models for upload/crop/process requests and responses (AC1, AC2)
- [ ] Create `src/api/routes.py` — `POST /api/upload` endpoint with file validation (magic bytes, size, format) (AC1)
- [ ] Create `static/index.html` — upload UI with file picker (AC1)
- [ ] Create `static/js/app.js` — upload handler, API calls (AC1)
- [ ] Create `static/css/style.css` — basic app styles (AC1)
- [ ] Implement `POST /api/crop` endpoint — accept image ID + crop coordinates, return cropped image (AC2)
- [ ] Create `static/js/crop.js` — Cropper.js integration for zoom/crop interaction (AC2)
- [ ] Write tests: `test_upload_valid_image`, `test_upload_invalid_file`, `test_upload_oversized` (AC1)
- [ ] Write tests: `test_crop_valid_region`, `test_crop_too_small` (AC2)

### Image Enhancement
- [ ] Create `src/processing/enhancement.py` — basic contrast + saturation enhancement in LAB space (AC3)
- [ ] Write tests: `test_enhancement_increases_contrast`, `test_enhancement_increases_saturation` (AC3)

### Color Quantization
- [ ] Create `src/processing/quantization.py` — K-means clustering in CIELAB space (AC4)
- [ ] Implement label assignment: colors 0–9, then A–J (AC4, AC5)
- [ ] Write tests: `test_quantization_returns_requested_colors`, `test_quantization_uses_lab_space`, `test_quantization_fewer_distinct_colors` (AC4)
- [ ] Write tests: `test_labels_single_char`, `test_labels_8_colors`, `test_labels_20_colors` (AC5)

### Grid Generation
- [ ] Create `src/processing/grid.py` — convert quantized image to 2D GridCell array at 4mm/50×65 (AC5)
- [ ] Write tests: `test_grid_dimensions_4mm`, `test_grid_all_cells_have_labels` (AC5)

### Preview Rendering
- [ ] Create `src/rendering/preview.py` — generate colored grid PNG from grid data (AC8)
- [ ] Implement `POST /api/process` — run enhance → quantize → grid → preview; return mosaic data (AC3–AC8)
- [ ] Implement `GET /api/preview/{mosaic_id}` — return preview PNG (AC8)
- [ ] Add preview display to frontend (AC8)
- [ ] Write tests: `test_preview_dimensions`, `test_preview_colors_match_palette` (AC8)
- [ ] Create golden reference fixtures for visual regression (AC8)

### PDF Generation
- [ ] Create `src/rendering/pdf.py` — ReportLab PDF: page 1 = numbered grid, page 2 = color legend (AC12)
- [ ] Implement grid page layout: 200mm × 263.5mm printable area, cells at 4mm (AC12)
- [ ] Implement legend page: color swatches with labels (AC12)
- [ ] Implement `GET /api/pdf/{mosaic_id}` endpoint (AC12)
- [ ] Add "Download PDF" button to frontend (AC12)
- [ ] Write tests: `test_pdf_two_pages`, `test_pdf_grid_page_dimensions`, `test_pdf_legend_has_all_colors` (AC12)

### Integration & QA
- [ ] Write integration test: `test_full_pipeline` — upload → crop → process → download PDF (AC1–AC12)
- [ ] Write integration test: `test_transparent_png_handling` (AC1)
- [ ] Manual QA: run through all 8 QA scenarios in Phase 1 doc
- [ ] Print test: print PDF at 100% scale, measure cells with ruler = 4mm

---

## Phase 2: Mosaic Modes & Color Refinement

### Circle Mosaic
- [ ] Create `src/rendering/grid_circle.py` — circle grid rendering with black inter-cell space (AC6)
- [ ] Add mosaic mode parameter to `POST /api/process` and schemas (AC6)
- [ ] Add mode toggle (square/circle) to frontend (AC6)
- [ ] Write tests: `test_circle_grid_dimensions`, `test_circle_rendering_has_black_gaps`, `test_circle_labels_centered` (AC6)
- [ ] Create circle mode golden reference fixtures (AC6)

### Size Selector
- [ ] Add component size parameter (4mm/5mm/6mm) to config, schemas, and `POST /api/process` (AC7)
- [ ] Update grid generation to use size-specific dimensions (50×65, 40×52, 33×43) (AC7)
- [ ] Add size dropdown to frontend (AC7)
- [ ] Update PDF layout to respect selected size (AC7)
- [ ] Write tests: `test_grid_dimensions_5mm`, `test_grid_dimensions_6mm`, `test_pdf_respects_size` (AC7)

### Advanced Enhancement
- [ ] Add CLAHE (adaptive contrast) to `enhancement.py` (AC3 improved)
- [ ] Add saturation curve adjustment (AC3 improved)
- [ ] Add edge-aware sharpening (bilateral filter + unsharp mask) (AC3 improved)
- [ ] Add before/after toggle to frontend
- [ ] Write tests: `test_clahe_improves_local_contrast`, `test_saturation_preserves_range` (AC3)

### Color Palette Editing
- [ ] Add palette display to frontend after processing (AC9)
- [ ] Implement color picker interaction (browser native `<input type="color">`) (AC9)
- [ ] Implement backend or frontend color swap — update grid cells + refresh preview (AC9)
- [ ] Add similar-color warning (LAB distance < threshold) (AC9)
- [ ] Write tests: `test_color_swap_updates_grid`, `test_similar_color_warning` (AC9)

### Integration & QA
- [ ] Write integration test: `test_pipeline_circle_mode` (AC6)
- [ ] Write integration test: `test_size_change_preserves_palette` (AC7, AC9)
- [ ] Write integration test: `test_color_edit_round_trip` (AC9)
- [ ] Manual QA: run through all 7 QA scenarios in Phase 2 doc

---

## Phase 3: Image Editing Tools

### Background Removal
- [ ] Create `src/processing/cutout.py` — wrap `rembg`; mask cleanup (feathering, smoothing) (AC10)
- [ ] Add `POST /api/cutout` endpoint (AC10)
- [ ] Add cutout button + mask preview to frontend (AC10)
- [ ] Document `rembg` model download in setup instructions (AC10)
- [ ] Write tests: `test_cutout_produces_rgba`, `test_cutout_mask_is_smooth` (AC10)

### Background Library & Upload
- [ ] Create `static/presets/` with 8–12 preset backgrounds (solids + gradients) (AC11)
- [ ] Add `GET /api/backgrounds` endpoint (AC11)
- [ ] Add background picker UI with thumbnails (AC11)
- [ ] Add custom background upload to `POST /api/upload` (with background flag) (AC11)
- [ ] Write tests: `test_preset_backgrounds_load`, `test_custom_background_validation` (AC11)

### Compositing
- [ ] Create `src/processing/compositing.py` — subject + background at position/scale (AC11)
- [ ] Add `POST /api/composite` endpoint (AC11)
- [ ] Create `static/js/editor.js` — drag-to-position, scale slider, live composite preview (AC11)
- [ ] Integrate editor step into frontend wizard (between crop and process) (AC11)
- [ ] Add undo/revert to original crop (AC10)
- [ ] Write tests: `test_composite_dimensions`, `test_composite_position`, `test_composite_scale`, `test_revert` (AC10, AC11)

### Integration & QA
- [ ] Write integration test: `test_cutout_to_pdf_pipeline` (AC10, AC11)
- [ ] Write integration test: `test_skip_editing_pipeline` (AC10, AC11 — optional path)
- [ ] Manual QA: run through all 8 QA scenarios in Phase 3 doc

---

## Phase 4: Export, Sharing & Persistence

### Persistence Layer
- [ ] Create `src/persistence/models.py` — SQLite schema: sessions, sheets (AC14)
- [ ] Create `src/persistence/storage.py` — CRUD operations for sessions and sheets (AC14)
- [ ] Add session cookie management (HttpOnly, SameSite, cryptographic UUID) (AC14)
- [ ] Implement `POST /api/sheets` — save current mosaic with full state (AC14)
- [ ] Implement `GET /api/sheets` — list saved sheets for current session (AC14)
- [ ] Implement `GET /api/sheets/{id}` — load saved sheet with full state restoration (AC14)
- [ ] Implement `DELETE /api/sheets/{id}` — delete sheet and clean up files (AC14)
- [ ] Copy images from temp to persistent storage on save (AC14)
- [ ] Write tests: `test_save_persists`, `test_list_session_only`, `test_load_restores_state`, `test_delete_cleans_up` (AC14)

### Sheet Management UI
- [ ] Add "Save Sheet" button + title input to frontend (AC14)
- [ ] Add "My Sheets" panel with thumbnails and titles (AC14)
- [ ] Add load, delete, and "New Sheet" actions (AC14)
- [ ] Add sheet count badge; show 20+ indicator (AC14, AC15 hook)
- [ ] Write test: `test_sheet_count_accurate` (AC14)

### Email PDF
- [ ] Create `src/email/sender.py` — send via transactional email provider (AC13)
- [ ] Add email provider config to `src/config.py` (AC13)
- [ ] Implement `POST /api/sheets/{id}/email` — validate address, rate limit, send PDF (AC13)
- [ ] Add "Email PDF" button + email input dialog to frontend (AC13)
- [ ] Handle unconfigured email provider gracefully (disable button) (AC13)
- [ ] Write tests: `test_email_validates_address`, `test_email_rate_limit`, `test_email_sends_pdf` (mocked) (AC13)

### Integration & QA
- [ ] Write integration test: `test_save_load_round_trip` (AC14)
- [ ] Write integration test: `test_multi_sheet_session` (AC14)
- [ ] Write integration test: `test_email_round_trip` (mocked) (AC13)
- [ ] Manual QA: run through all 8 QA scenarios in Phase 4 doc

---

## Phase 5: Print-on-Demand Integration

### Lulu Research & Setup
- [ ] Research Lulu API: product types, specifications, auth, endpoints (AC15)
- [ ] Document exact Lulu product ID for spiral-bound US Letter color book (AC15)
- [ ] Create `src/book/specs.py` — Lulu print specs (bleed, margins, DPI, color profile) (AC15)

### Book Assembly
- [ ] Create `src/book/cover.py` — cover page generation (title, optional collage) (AC15)
- [ ] Create `src/book/assembly.py` — assemble interior PDF: title page + alternating legend/grid (AC15)
- [ ] Handle even page count requirement (pad with blank if needed) (AC15)
- [ ] Write tests: `test_book_page_count`, `test_book_page_order`, `test_first_page_is_title`, `test_even_page_padding` (AC15)

### Book Builder UI
- [ ] Create `static/js/book.js` — sheet selector, drag-to-reorder (AC15)
- [ ] Implement `POST /api/book/preview` — book layout preview with page thumbnails (AC15)
- [ ] Implement `POST /api/book/assemble` — generate print-ready PDF (AC15)
- [ ] Implement `GET /api/book/assemble/{id}` — download assembled book for review (AC15)
- [ ] Enforce minimum 20 sheets for book order (AC15)

### Lulu API Integration
- [ ] Create `src/book/lulu.py` — Lulu API client (create job, upload files, pricing, order, status) (AC15)
- [ ] Implement `POST /api/book/order` — submit to Lulu, return checkout URL (AC15)
- [ ] Implement `GET /api/book/order/{id}/status` — query and display order status (AC15)
- [ ] Add order button, redirect to Lulu checkout, status display to frontend (AC15)
- [ ] Write tests (Lulu mocked): `test_lulu_order_flow`, `test_lulu_status_check`, `test_lulu_error_handling` (AC15)

### Integration & QA
- [ ] Write integration test: `test_book_assembly_end_to_end` (AC15)
- [ ] Manual QA: run through all 8 QA scenarios in Phase 5 doc
