# Mosaic Coloring App

A web application that converts uploaded photos into mosaic color-by-number coloring sheets. Users upload a photo, crop it, choose mosaic parameters, and receive a printable PDF with a numbered grid and color legend — ready for US Letter paper.

## What It Does

1. **Upload** a JPEG or PNG photo (up to 20 MB)
2. **Crop** the region of interest using an interactive cropper
3. **Configure** the mosaic: number of colors (8–20), component size (3–5 mm), and shape mode (square, circle, or hexagon)
4. **Generate** — the pipeline enhances the image, quantizes colors via K-means in CIELAB space, and maps pixels to a numbered grid
5. **Preview** the mosaic with an interactive color palette editor
6. **Download** a two-page PDF (grid page + color legend)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 · FastAPI · Uvicorn |
| Frontend | Vanilla HTML/JS/CSS · Cropper.js |
| Image processing | Pillow · OpenCV · scikit-learn (K-means) |
| PDF generation | ReportLab |

## Repository Structure

```
coloring-app/
├── src/                    # Application source code
│   ├── main.py             # FastAPI app entry point, lifespan, middleware
│   ├── config.py           # Environment-driven configuration constants
│   ├── api/
│   │   ├── routes.py       # API endpoints (upload, crop, process, preview, PDF, palette edit)
│   │   └── schemas.py      # Pydantic request/response models
│   ├── models/
│   │   └── mosaic.py       # Core data models (ColorPalette, GridCell, MosaicSheet)
│   ├── processing/
│   │   ├── enhancement.py  # Adaptive contrast, saturation, edge sharpening
│   │   ├── quantization.py # K-means color quantization in CIELAB
│   │   └── grid.py         # Grid generation from label maps
│   └── rendering/
│       ├── preview.py      # PNG preview rendering
│       ├── pdf.py          # ReportLab PDF generation (grid + legend)
│       ├── geometry.py     # Hexagon vertex math
│       └── color_utils.py  # Perceived brightness for label contrast
├── static/                 # Frontend served by FastAPI's StaticFiles
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── app.js          # Step navigation, API calls, palette editing
│       └── crop.js         # Cropper.js integration
├── tests/                  # Pytest test suite
├── docs/                   # Project documentation and phase plans
├── pyproject.toml          # Project metadata, pytest/ruff config
├── requirements.txt        # Runtime dependencies
└── requirements-dev.txt    # Dev/test dependencies
```

## Prerequisites

- Python 3.12+
- A virtual environment tool (`python -m venv`)

## Local Setup

```bash
# Clone the repository
git clone <repo-url> && cd coloring-app

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# (Optional) Install dev/test dependencies
pip install -r requirements-dev.txt
```

## Running the App

With the virtual environment active:

```bash
uvicorn src.main:app --reload
```

> **Note (Phase 3 — Image Editing):** The background-removal feature uses
> [rembg](https://github.com/danielgatis/rembg) with the U2-Net model (~170 MB).
> The model is downloaded automatically on first use. To pre-download it:
>
> ```bash
> python -c "from rembg import new_session; new_session('u2net')"
> ```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in a browser.

FastAPI auto-generated API docs are at:
- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

## Configuration

All settings are environment variables with sensible defaults:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_UPLOAD_SIZE_MB` | `20` | Maximum upload file size |
| `MAX_IMAGE_DIMENSION` | `4000` | Max image width or height (pixels); larger images are downscaled |
| `COLORING_TEMP_DIR` | System temp dir | Base directory for temporary image storage |
| `TEMP_TTL_SECONDS` | `3600` | Time-to-live for temp files before cleanup |
| `TEMP_CLEANUP_INTERVAL_SECONDS` | `300` | Interval between cleanup sweeps |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8000` | Comma-separated list of allowed CORS origins |

## Running Tests

```bash
pytest
```

See [docs/QA.md](docs/QA.md) for detailed test commands, fixtures, and per-file coverage information.

## Further Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design, data flow, and component overview
- [CODEBASE_CONTEXT.md](CODEBASE_CONTEXT.md) — Structured facts for AI agents working in this repo
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common issues and fixes
- [docs/QA.md](docs/QA.md) — QA guide with setup, testing, and configuration reference
- [docs/phases/PHASES_OVERVIEW.md](docs/phases/PHASES_OVERVIEW.md) — Product roadmap and phase plans
