# Phase 1: Core Pipeline POC

**Status**: Not Started
**Dependencies**: None
**Cross-references**: [PHASES_OVERVIEW.md](PHASES_OVERVIEW.md)

---

## Goal

Build the end-to-end proof of concept: a user uploads a photo, crops it, the app enhances and quantizes it to a chosen number of colors, generates a square pixel grid with single-character labels, displays an on-screen preview, and exports a two-page PDF (grid + legend).

This phase proves the image processing pipeline works and produces usable coloring sheets.

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC1.1 | User can upload a photo (JPEG, PNG) via the web interface |
| AC1.2 | User can zoom and crop to select a rectangular region of the photo |
| AC1.3 | App applies basic contrast and saturation enhancement to the cropped image |
| AC1.4 | User selects number of colors (8–20 via slider or input) |
| AC1.5 | App quantizes the enhanced image to the selected number of colors using K-means in CIELAB color space |
| AC1.6 | App generates a square pixel grid at 3mm component size (60 columns × 80 rows) |
| AC1.7 | Each cell displays a single-character label (0–9, then A–J) corresponding to its color |
| AC1.8 | User sees an on-screen preview of the generated mosaic grid |
| AC1.9 | User can download a PDF: page 1 = numbered grid, page 2 = color legend with swatches and labels |
| AC1.10 | The PDF grid fills the printable area (180mm × 240mm) on US Letter paper |

## Architecture

### Project Structure

```
coloring-app/
├── src/
│   ├── main.py                  # FastAPI app entry point, serves static files + API
│   ├── config.py                # All configurable constants (grid sizes, margins, color range)
│   ├── api/
│   │   ├── routes.py            # API endpoints: upload, process, download
│   │   └── schemas.py           # Pydantic request/response models
│   ├── processing/
│   │   ├── enhancement.py       # Contrast/saturation enhancement
│   │   ├── quantization.py      # K-means color quantization in LAB space
│   │   └── grid.py              # Grid generation (image → cell matrix)
│   ├── rendering/
│   │   ├── preview.py           # Generate preview image for web display
│   │   └── pdf.py               # ReportLab PDF generation (grid page + legend page)
│   └── models/
│       └── mosaic.py            # Data classes: ColorPalette, GridCell, MosaicSheet
├── static/
│   ├── index.html               # Single-page UI
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── app.js               # Main app logic, API calls
│       └── crop.js              # Cropper.js integration
├── tests/
│   ├── fixtures/                # Test images
│   ├── golden/                  # Golden reference outputs for visual regression
│   ├── test_enhancement.py
│   ├── test_quantization.py
│   ├── test_grid.py
│   └── test_pdf.py
├── requirements.txt
└── pyproject.toml
```

### API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/upload` | Accept image file, return image ID and dimensions |
| POST | `/api/crop` | Accept image ID + crop coordinates, return cropped image ID |
| POST | `/api/process` | Accept cropped image ID + color count, run enhancement → quantization → grid; return mosaic data + preview |
| GET | `/api/preview/{mosaic_id}` | Return preview image (PNG) |
| GET | `/api/pdf/{mosaic_id}` | Return generated PDF |

### Data Flow

```
Upload (JPEG/PNG)
  → Store original in temp directory
  → Crop to user-selected region
  → Enhance (contrast + saturation in LAB space)
  → Quantize (K-means, N clusters, LAB space)
  → Build grid (assign each pixel region to nearest palette color)
  → Render preview (colored grid image for web display)
  → Render PDF (grid page with labels + legend page with swatches)
```

### Key Design Decisions

1. **LAB color space for quantization**: K-means in RGB produces perceptually uneven clusters. CIELAB is perceptually uniform — similar LAB distances mean similar perceived colors.
2. **Single-character labels**: `0–9` then `A–J` covers 20 colors max. Fits comfortably in 3mm cells.
3. **Temp file storage**: Phase 1 uses filesystem temp directory (`tempfile`). No database. Each upload gets a UUID directory.
4. **Grid-first approach**: The grid is the core data structure — a 2D array of `GridCell` objects, each holding (row, col, color_index, label). All rendering (preview, PDF) reads from this grid.
5. **3mm only in Phase 1**: Size selector (4mm, 5mm, 6mm) deferred to Phase 2 to keep POC focused.

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Very small crop region (< 50px wide) | Reject with error: "Crop region too small for grid generation" |
| Monochrome/low-contrast image | Enhancement will boost contrast, but warn if quantization produces fewer distinct colors than requested |
| Transparent PNG | Convert to RGB with white background before processing |
| Very large image (> 20MP) | Resize to max 4000px on longest side before processing |
| Requested colors > distinct colors in image | K-means will produce fewer clusters; return actual count used |
| Non-image file upload | Validate MIME type; reject with 400 error |
| Concurrent uploads | UUID-based temp directories prevent collision |

## Error Handling Strategy

- **Recoverable**: Invalid crop coordinates → return 400 with descriptive message. Image too small → suggest larger crop.
- **Fatal**: Disk full, processing crash → return 500, log full traceback, clean up temp files.
- All errors logged via Python `logging` module (per style guide). Never `print()`.

## Security Considerations

- Validate uploaded file is actually an image (check magic bytes, not just extension)
- Limit upload size (configurable, default 20MB)
- Sanitize filenames; use UUIDs for storage
- Temp files cleaned up on configurable TTL
- No user input passed to shell commands

## Observability

- Log each pipeline step with timing: upload, crop, enhance, quantize, grid, render
- Log image dimensions, color count, grid size at each step
- Log errors with full context (image ID, step that failed, input parameters)

## Test Plan

### Unit Tests

| Test | Maps to | Description |
|------|---------|-------------|
| `test_enhancement_increases_contrast` | AC1.3 | Given a low-contrast image, when enhanced, then standard deviation of pixel values increases |
| `test_enhancement_increases_saturation` | AC1.3 | Given a desaturated image, when enhanced, then mean saturation in HSV increases |
| `test_quantization_returns_requested_colors` | AC1.5 | Given an image and N=12, when quantized, then palette has exactly 12 colors |
| `test_quantization_uses_lab_space` | AC1.5 | Given two perceptually similar RGB colors, when quantized, they merge into one cluster |
| `test_grid_dimensions` | AC1.6 | Given a cropped image, when grid is built at 3mm, then grid is 60 columns × 80 rows |
| `test_grid_labels_single_char` | AC1.7 | Given 20 colors, when labels assigned, then all labels are single characters 0-9, A-J |
| `test_grid_labels_8_colors` | AC1.7 | Given 8 colors, when labels assigned, then labels are 0-7 |
| `test_pdf_two_pages` | AC1.9 | Given a mosaic, when PDF generated, then PDF has exactly 2 pages |
| `test_pdf_grid_page_dimensions` | AC1.10 | Given a mosaic, when PDF generated, then grid area is 180mm × 240mm |
| `test_pdf_legend_has_all_colors` | AC1.9 | Given a 15-color mosaic, when PDF generated, then legend page shows 15 swatches with correct labels |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_full_pipeline` | Upload fixture image → crop → process with 12 colors → verify PDF downloads successfully |
| `test_upload_invalid_file` | Upload a text file → verify 400 response |
| `test_crop_too_small` | Upload, then crop to 10×10px region → verify descriptive error |

### Visual Regression

- Generate grid PNG from fixture image with fixed seed (deterministic K-means)
- Compare pixel-by-pixel against golden reference
- Threshold: < 1% pixel difference (accounts for platform rendering differences)

### Top 5 High-Value Test Cases

1. **Given** a 1200×800 photo of a landscape, **When** cropped to center 800×600, enhanced, and quantized to 12 colors, **Then** the grid is 60×80, all cells have labels 0-9/A-B, and PDF has 2 pages with correct dimensions.

2. **Given** a nearly monochrome photo, **When** quantized to 15 colors, **Then** the app returns fewer colors than requested and the grid/legend reflect the actual count.

3. **Given** a transparent PNG, **When** uploaded, **Then** transparency is replaced with white and processing succeeds normally.

4. **Given** a 30MB JPEG, **When** uploaded, **Then** the app rejects it with a clear file-size error.

5. **Given** a valid upload, **When** the full pipeline runs, **Then** each step (enhance, quantize, grid, render) is logged with timing information.

## QA Manual Test Scenarios

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| QA1 | Basic upload | Open web UI, click upload, select a JPEG photo | Photo displays in the crop interface |
| QA2 | Crop interaction | Drag to select a region, zoom in/out | Crop overlay updates; selected region highlighted |
| QA3 | Process with defaults | Set color count to 12, click Process | Loading indicator → preview of colored pixel grid appears |
| QA4 | Verify grid labels | Zoom into preview | Each cell shows a single character (0-9 or A-J) |
| QA5 | Download PDF | Click Download PDF | Browser downloads a PDF; page 1 = grid, page 2 = legend |
| QA6 | Print test | Print the PDF at 100% scale | Measure grid cells with ruler — should be 3mm × 3mm |
| QA7 | Color count range | Try 7 (below min), 8, 20, 21 (above max) | 7 and 21 rejected; 8 and 20 accepted |
| QA8 | Error handling | Upload a .txt file | Clear error message displayed |
