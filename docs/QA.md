# QA Guide: Mosaic Coloring App

## Prerequisites

Python 3.12+ is required. All commands assume you are in the repo root (`/path/to/coloring-app`).

---

## Setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Web App

Start the development server from the repo root with the virtual environment active:

```bash
uvicorn src.main:app --reload
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

The `--reload` flag enables auto-reload on code changes. To specify a different host or port:

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### API docs

FastAPI's auto-generated API documentation is available at:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Configuration (environment variables)

| Variable | Default | Description |
|---|---|---|
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum upload size in megabytes |
| `MAX_IMAGE_DIMENSION` | `4000` | Maximum image width or height in pixels |
| `COLORING_TEMP_DIR` | system temp dir | Base directory for temporary files |
| `TEMP_TTL_SECONDS` | `3600` | How long temp files are kept (seconds) |
| `TEMP_CLEANUP_INTERVAL_SECONDS` | `300` | How often cleanup runs (seconds) |
| `CONTRAST_FACTOR` | `1.3` | Image contrast enhancement multiplier |
| `SATURATION_FACTOR` | `1.3` | Image saturation enhancement multiplier |

---

## Running the Test Suite

With the virtual environment active, run all tests from the repo root:

```bash
pytest
```

### Common pytest flags

| Command | What it does |
|---|---|
| `pytest` | Run all tests |
| `pytest -v` | Verbose output (shows each test name) |
| `pytest -x` | Stop after the first failure |
| `pytest --tb=short` | Shorter traceback format |
| `pytest tests/test_integration.py` | Run only integration tests |
| `pytest tests/test_enhancement.py` | Run only enhancement unit tests |
| `pytest -k "test_upload"` | Run tests whose name contains "test_upload" |

### Test files and what they cover

| File | Coverage area |
|---|---|
| `tests/test_integration.py` | Full API pipeline: upload → crop → process → preview → PDF |
| `tests/test_enhancement.py` | Image contrast and saturation enhancement (`ImageEnhancer`) |
| `tests/test_quantization.py` | Color quantization and palette generation (`ColorQuantizer`) |
| `tests/test_grid.py` | Grid generation logic (`GridGenerator`) |
| `tests/test_preview.py` | PNG preview rendering (`PreviewRenderer`) |
| `tests/test_pdf.py` | PDF coloring sheet rendering (`PdfRenderer`) |

### Shared test fixtures (conftest.py)

| Fixture | Description |
|---|---|
| `sample_rgb_image` | 200×150 image with four distinct color quadrants |
| `low_contrast_image` | 200×150 near-grayscale image for contrast tests |
| `small_image` | 30×30 image for edge-case tests |
| `transparent_png_image` | 100×100 RGBA image with transparency |

---

## Manual QA Walkthrough

The app exposes a single-page UI at the root URL. Walk through these steps to verify the full pipeline:

### Step 1: Upload

1. Click **Choose Photo**.
2. Select a JPEG or PNG file (max 20 MB).
3. **Expected**: The image appears in the crop view.
4. **Error cases to verify**: uploading a non-image file (e.g. a `.txt`) or a file over 20 MB should show an error message without crashing.

### Step 2: Crop

1. Use the crop handles to select a region of interest.
2. Click **Crop**.
3. **Expected**: The crop is confirmed and the color-count slider appears.
4. **Edge case**: crop region smaller than 50×50 pixels should be rejected with an error.

### Step 3: Process

1. Adjust the **Number of Colors** slider (8–20).
2. Click **Generate**.
3. **Expected**: A color-by-number preview image is displayed alongside a color legend, and the **Download PDF** button becomes active.

### Step 4: Download PDF

1. Click **Download PDF**.
2. **Expected**: A printable US Letter PDF downloads containing the mosaic grid and color legend.

---

## API Endpoint Reference

All endpoints are under the `/api` prefix.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload a JPEG/PNG; returns `image_id`, `width`, `height` |
| `POST` | `/api/crop` | Crop an uploaded image; body: `CropRequest` |
| `POST` | `/api/process` | Run enhancement, quantization, grid generation |
| `GET` | `/api/preview/{image_id}` | Return PNG preview of the mosaic |
| `GET` | `/api/pdf/{image_id}` | Return the printable PDF |

Validation rules enforced by the API:
- Upload accepts only `image/jpeg` and `image/png` MIME types, verified by magic bytes.
- Crop coordinates must be within image bounds; width/height must each be at least 50 pixels.
- Color count must be between 8 and 20.
- `image_id` must be a valid hex UUID; any other value returns HTTP 400.
- Unknown `image_id` values return HTTP 404.

---

## Linting

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and import sorting.

```bash
# Check for lint errors
ruff check .

# Auto-fix fixable issues
ruff check . --fix
```
