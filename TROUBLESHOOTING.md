# Troubleshooting

## Local Setup

### `ModuleNotFoundError: No module named 'src'`

**Symptom**: Running `pytest` or `uvicorn src.main:app` raises `ModuleNotFoundError`.

**Cause**: The virtual environment is not activated, or `pythonpath` is not set correctly.

**Fix**:
```bash
source .venv/bin/activate
```
Pytest is configured with `pythonpath = ["."]` in `pyproject.toml`, so it should find `src` as long as you run from the repo root.

---

### `pip install` fails for OpenCV or scikit-learn

**Symptom**: Build errors when installing `opencv-python-headless` or `scikit-learn`.

**Cause**: Missing Python 3.12+ or incompatible system libraries.

**Fix**: Ensure Python 3.12+ is installed. On macOS:
```bash
python --version   # Must be 3.12+
```
If using `pyenv`, confirm the correct version is active:
```bash
pyenv version
```

---

### `ValueError: Environment variable ... is not a valid integer`

**Symptom**: App crashes on startup with a `ValueError` about an environment variable.

**Cause**: An environment variable like `MAX_UPLOAD_SIZE_MB` or `TEMP_TTL_SECONDS` is set to a non-integer value.

**Fix**: Unset the offending variable or correct its value:
```bash
unset MAX_UPLOAD_SIZE_MB
# or
export MAX_UPLOAD_SIZE_MB=20
```

---

### `ValueError: TEMP_DIR parent does not exist` or `not writable`

**Symptom**: App fails at startup in `validate_config()`.

**Cause**: The `COLORING_TEMP_DIR` environment variable points to a non-existent or read-only path.

**Fix**: Either unset the variable (to use the system temp dir) or create the directory:
```bash
unset COLORING_TEMP_DIR
# or
mkdir -p /your/custom/temp && export COLORING_TEMP_DIR=/your/custom/temp
```

---

## Runtime Errors

### Upload returns 400 `"File is not a valid JPEG or PNG image"`

**Symptom**: Uploading a file that appears to be an image returns a 400 error.

**Cause**: The server validates magic bytes (first 3–8 bytes), not the file extension. The file may be a renamed non-image, a WebP, or a corrupt file.

**Fix**: Ensure the file is a genuine JPEG or PNG. Convert other formats first:
```bash
# Example: convert WebP to PNG
convert input.webp output.png
```

---

### Upload returns 400 `"File too large"`

**Symptom**: Large image uploads are rejected.

**Cause**: The file exceeds `MAX_UPLOAD_SIZE_MB` (default: 20 MB).

**Fix**: Resize or compress the image before uploading, or increase the limit:
```bash
export MAX_UPLOAD_SIZE_MB=50
```

---

### Process returns 400 `"Unsupported size/mode combination"`

**Symptom**: The `/api/process` endpoint rejects a request.

**Cause**: The `(size, mode)` pair is not in the `GRID_DIMENSIONS` lookup table. Valid combinations are sizes 3, 4, or 5 with modes `square`, `circle`, or `hexagon`.

**Fix**: Use one of the supported combinations. The frontend enforces this via its dropdowns and radio buttons.

---

### Preview image shows no labels (tiny or blank text)

**Symptom**: The preview PNG renders but cell labels are invisible.

**Cause**: TrueType fonts are not found on the system. The renderer falls back to a default bitmap font which may not scale well.

**Fix**: Install DejaVu fonts (Linux) or ensure Helvetica is available (macOS):
```bash
# Ubuntu/Debian
sudo apt install fonts-dejavu-core
```
On macOS, Helvetica is bundled with the OS — this should work out of the box.

---

### `Mosaic '{id}' not found` (404) on PDF download

**Symptom**: Clicking "Download PDF" returns a 404 after the mosaic was generated.

**Cause**: The in-memory mosaic store has a max capacity of 100 entries with LRU eviction. If the server restarted, or 100+ mosaics were created since, the entry was evicted.

**Fix**: Re-run the processing step to generate a new mosaic. This is expected behavior for Phase 1 (no persistence layer).

---

## Testing

### Tests fail with `fixture 'client' not found`

**Symptom**: Pytest cannot find shared fixtures.

**Cause**: Running pytest from a directory other than the repo root, or `conftest.py` is missing.

**Fix**: Always run pytest from the repo root:
```bash
cd /path/to/coloring-app
pytest
```

---

### Image comparison tests fail after changing rendering code

**Symptom**: Tests in `test_preview.py` or `test_pdf.py` produce different output than expected.

**Cause**: Rendering changes (font, spacing, colors) naturally alter output. Golden files in `tests/golden/` may need updating.

**Fix**: Visually inspect the new output. If it looks correct, update the golden files. See [docs/QA.md](docs/QA.md) for test details.
