# Phase 3: Image Editing Tools

**Status**: Not Started
**Dependencies**: Phase 1 (Core Pipeline POC)
**Cross-references**: [PHASES_OVERVIEW.md](PHASES_OVERVIEW.md) | [PHASE_1_CORE_PIPELINE.md](PHASE_1_CORE_PIPELINE.md)

---

## Goal

Add pre-processing image editing tools that run before the image enters the quantization pipeline: subject cutout (background removal), preset background library, custom background upload, and position/scale compositing. These tools let users isolate a subject from a busy background and place it on a cleaner one that produces better coloring sheets.

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC3.1 | User can activate a cutout tool that removes the background from the cropped image |
| AC3.2 | Background removal produces a clean subject mask with smooth edges (feathered, not jagged) |
| AC3.3 | User can choose from a library of preset solid-color and simple gradient backgrounds |
| AC3.4 | User can upload a custom image to use as background |
| AC3.5 | User can position and scale the cutout subject on the chosen background |
| AC3.6 | User can see a live composite preview before proceeding to quantization |
| AC3.7 | The composite image feeds into the existing enhancement → quantization → grid pipeline unchanged |
| AC3.8 | User can undo cutout and revert to the original cropped image |
| AC3.9 | Cutout tool works on common subjects: people, pets, objects against varied backgrounds |

## Architecture Changes

### New/Modified Files

| File | Change |
|------|--------|
| `src/processing/cutout.py` | New — wraps `rembg` for background removal; mask cleanup (feathering, smoothing) |
| `src/processing/compositing.py` | New — composite subject onto background at given position/scale |
| `src/api/routes.py` | New endpoints: `/api/cutout`, `/api/backgrounds`, `/api/composite` |
| `src/api/schemas.py` | Add `CutoutRequest`, `CompositeRequest`, `BackgroundInfo` models |
| `static/presets/` | New directory — preset background images (solid colors, gradients) |
| `static/js/editor.js` | New — cutout button, background picker, drag-to-position, scale slider |
| `static/js/app.js` | Integrate editor step between crop and process |
| `static/css/style.css` | Styles for editor panel, background thumbnails, position overlay |

### API Endpoints (New)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/cutout` | Accept cropped image ID; run background removal; return cutout image ID + mask |
| GET | `/api/backgrounds` | List available preset backgrounds (name, thumbnail URL) |
| POST | `/api/composite` | Accept cutout ID + background ID/upload + position/scale; return composite image ID |

### Background Removal Approach

- Use `rembg` library (U2-Net model) — works offline, no API key needed
- Post-process the alpha mask: Gaussian blur for feathering, morphological operations for edge cleanup
- Return both the masked subject (RGBA) and the binary mask for UI display
- The `rembg` model download (~170MB) happens on first use; document this in setup instructions

### Compositing

- Subject placed on background at user-specified (x, y) offset and scale factor
- Scale: 0.25× to 2.0× range, default 1.0×
- Position: drag interaction on frontend, sends pixel offsets
- Result is a flat RGB image at the same resolution as the original crop — then it enters the existing pipeline as if it were the cropped image

### Preset Background Library

- 8–12 preset backgrounds shipped with the app:
  - Solid colors: white, light gray, sky blue, pale yellow, mint green, light pink
  - Simple gradients: blue-to-white, sunset (orange-pink), forest (green gradient)
- Stored as 1200×1200 JPEG/PNG files in `static/presets/`
- Custom upload backgrounds resized to match composite dimensions

### User Flow

```
Upload → Crop → [Optional: Cutout → Choose Background → Position/Scale → Composite] → Enhance → Quantize → Grid → Preview → PDF
```

The editing step is optional — user can skip directly from crop to processing.

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Image with no clear foreground subject | `rembg` may produce poor mask — show preview of mask so user can decide to proceed or skip |
| Subject touching crop edges | Mask may clip subject — warn user to crop with margin around subject |
| Custom background smaller than composite area | Tile or scale-to-fill; default to scale-to-fill |
| Custom background much larger | Center-crop to match composite dimensions |
| Subject scale results in overflow beyond canvas | Clip to canvas bounds; warn if significant portion is clipped |
| Undo after composite | Restore the original cropped image; discard cutout and composite |
| Multiple cutout attempts | Allow re-running cutout (e.g., after re-cropping) |

## Security Considerations

- Custom background uploads go through the same validation as photo uploads (magic bytes, size limit, image format check)
- Preset backgrounds are static files — no user input in file paths
- `rembg` runs locally — no data sent to external services

## Test Plan

### Unit Tests

| Test | Maps to |
|------|---------|
| `test_cutout_produces_rgba` | AC3.1 — output has alpha channel |
| `test_cutout_mask_is_smooth` | AC3.2 — no jagged edges (edge gradient check) |
| `test_composite_dimensions_match_crop` | AC3.7 — output same size as input crop |
| `test_composite_subject_position` | AC3.5 — subject placed at specified offset |
| `test_composite_subject_scale` | AC3.5 — subject scaled correctly |
| `test_preset_backgrounds_load` | AC3.3 — all presets exist and are valid images |
| `test_revert_restores_original` | AC3.8 — after undo, image matches original crop |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_cutout_to_pdf_pipeline` | Upload → crop → cutout → preset background → composite → process → PDF downloads successfully |
| `test_skip_editing_pipeline` | Upload → crop → process (skip cutout) → PDF downloads — editing tools are truly optional |
| `test_custom_background_upload` | Upload photo → cutout → upload custom background → composite → verify composite is valid |

### Top 5 High-Value Test Cases

1. **Given** a photo of a pet against a cluttered background, **When** cutout tool is applied and pet is placed on a white background, **Then** the resulting coloring sheet has a clean subject with no background noise.

2. **Given** a cutout subject, **When** user scales to 1.5× and drags to upper-left, **Then** the composite preview shows the subject correctly positioned and scaled, and the final grid reflects this layout.

3. **Given** a processed mosaic (post-cutout), **When** user clicks undo, **Then** the original cropped image is restored and the editing panel resets.

4. **Given** a photo with no clear foreground, **When** cutout is applied, **Then** user sees the mask preview and can choose to accept or revert.

5. **Given** a custom background upload that is 400×400px and a crop that is 1200×800, **When** composite is created, **Then** the background is scaled to fill 1200×800 without distortion (center-crop).

## QA Manual Test Scenarios

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| QA1 | Cutout activation | Upload photo, crop, click "Cut Out Subject" | Subject isolated with transparent background; preview shows mask overlay |
| QA2 | Preset backgrounds | After cutout, click through preset background options | Background changes behind subject in real-time preview |
| QA3 | Custom background | After cutout, click "Upload Background", select an image | Custom image appears behind subject |
| QA4 | Position and scale | Drag subject around; adjust scale slider | Subject moves and resizes in preview |
| QA5 | Proceed to mosaic | After compositing, click Process | Mosaic generates from the composite image |
| QA6 | Undo cutout | After compositing, click Undo/Revert | Returns to original cropped image; editor panel resets |
| QA7 | Skip editing | Upload, crop, click Process directly (skip cutout) | Works exactly as Phase 1 — editing is optional |
| QA8 | Poor cutout quality | Upload image with no clear subject, apply cutout | Mask preview shows; user can evaluate and revert if poor |
