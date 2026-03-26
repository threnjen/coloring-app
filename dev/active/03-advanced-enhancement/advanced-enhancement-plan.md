# 03: Advanced Enhancement — Plan

**Status**: Not Started
**Dependencies**: Phase 1 (complete)
**Blocked by**: None (fully independent)
**Blocks**: Nothing

---

## Requirements & Traceability

### Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC2.5 | App applies advanced enhancement: adaptive contrast (CLAHE), saturation curves, edge-aware sharpening |

### Non-Goals

- No mosaic mode changes
- No size selector changes
- No color palette editing
- No change to quantization algorithm
- Enhancement parameters are not user-configurable in this feature (use sensible defaults)

### Traceability

| AC | Code Areas | Planned Tests |
|----|------------|---------------|
| AC2.5 (CLAHE) | `src/processing/enhancement.py` `_enhance_contrast` | `test_clahe_improves_local_contrast`, `test_clahe_preserves_dimensions` |
| AC2.5 (saturation) | `src/processing/enhancement.py` `_enhance_saturation` | `test_saturation_curve_boosts_midrange`, `test_saturation_preserves_range` |
| AC2.5 (sharpening) | `src/processing/enhancement.py` (new method) | `test_edge_sharpening_increases_detail`, `test_edge_sharpening_no_noise_amplification` |
| AC2.5 (before/after) | `src/api/routes.py`, `static/js/app.js` | `test_before_after_images_different` |

---

## Stage 0: Test Prerequisites

**Goal**: Existing enhancement tests pass; new tests written and failing
**Success Criteria**: 4 existing tests green; new enhancement tests red
**Status**: Not Started

- Existing tests: `test_enhancement_increases_contrast`, `test_enhancement_increases_saturation`, `test_enhancement_preserves_dimensions`, `test_enhancement_returns_rgb`
- These tests will need updating — they test the old enhancement behavior; the new CLAHE approach may change what's measured
- Write new failing tests first, then update or replace old tests as implementation changes

## Stage 1: Replace Contrast Enhancement with CLAHE

**Goal**: Replace global contrast scaling with CLAHE
**Success Criteria**: `_enhance_contrast` uses `cv2.createCLAHE`; local contrast (measured by local variance of L channel) increases more than global method
**Status**: Not Started

### Design

Current `_enhance_contrast`:
- Converts to LAB, scales L channel around mean by `contrast_factor`
- This is a global operation — uniform across the image

New `_enhance_contrast`:
- Convert to LAB
- Apply `cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))` to L channel
- Convert back
- `clipLimit` and `tileGridSize` as class-level constants (not constructor params for now)

### Correctness

- CLAHE clip limit prevents over-amplification in homogeneous regions
- Tile grid size 8×8 is standard; smaller tiles = more local, but slower
- The existing `contrast_factor` config param becomes unused — remove from `__init__` or keep as fallback

## Stage 2: Replace Saturation Enhancement with Saturation Curve

**Goal**: Replace linear saturation scaling with a curve that boosts mid-range more
**Success Criteria**: Mid-saturation pixels get boosted more than already-saturated pixels; no channel clipping
**Status**: Not Started

### Design

Current `_enhance_saturation`:
- Converts to HSV, multiplies S channel by `saturation_factor`, clips to 255

New `_enhance_saturation`:
- Convert to HSV
- Apply a curve to S channel: `S_new = S + boost × S × (1 - S/255)`
- This boosts low/mid saturation more than high saturation (diminishing returns near 255)
- `boost` factor as class constant (default ~0.4)
- Clip to [0, 255] as safety net

### Correctness

- The curve `S + boost × S × (1 - S/255)` is monotonically increasing for boost > 0
- At S=0: no change (black stays black)
- At S=255: S_new = 255 (fully saturated stays the same)
- At S=128: S_new ≈ 128 + 0.4 × 128 × 0.498 ≈ 153 (noticeable boost)
- No clipping if boost ≤ 1.0

## Stage 3: Add Edge-Aware Sharpening

**Goal**: Add a sharpening step that enhances details without amplifying noise
**Success Criteria**: Edge regions are sharper; flat regions are not noisier
**Status**: Not Started

### Design

Two-step approach:
1. **Bilateral filter**: `cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)` — smooths while preserving edges
2. **Unsharp mask**: `sharpened = img + alpha × (img - blurred)` where blurred is the bilateral output, alpha ~0.5

Add as `_sharpen` method, called after contrast and saturation in `enhance()`.

### Correctness

- Bilateral filter is slow on large images — but images are already capped at 4000px max dimension
- Alpha should be modest (0.3–0.5) to avoid halo artifacts
- Clip result to [0, 255]
- The order matters: contrast → saturation → sharpening (sharpen last to preserve the enhanced details)

## Stage 4: Before/After Toggle (UI)

**Goal**: User can compare pre-enhancement vs post-enhancement preview
**Success Criteria**: UI shows a toggle; clicking it swaps between original crop and enhanced version
**Status**: Not Started

### Design

- In `_run_pipeline`, save the cropped image (pre-enhancement) as an additional preview
- Store both images in temp directory: `pre_enhance.png` and the normal preview
- New API endpoint: `GET /api/preview/{mosaic_id}/original` — returns the cropped (unenhanced) image resized to preview dimensions
- UI: add a toggle button/checkbox "Show original" in the preview step
- Toggle swaps `previewImage.src` between `/api/preview/{mosaic_id}` and `/api/preview/{mosaic_id}/original`

---

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Already high-contrast image | CLAHE with clip limit prevents over-enhancement |
| Already saturated image | Curve naturally applies less boost at high S values |
| Very dark/very bright image | CLAHE handles this well (per-tile equalization) |
| Large image (4000px) | Bilateral filter may be slow (~1-2s) but acceptable for a one-time process |
| Enhancement makes colors less distinct | Unlikely with CLAHE + saturation boost; if quantized palette has poor separation, that's a quantization issue |

## Clean Design Checklist

- [ ] Enhancement parameters are class-level constants, not constructor args (simplicity)
- [ ] Remove or deprecate `CONTRAST_FACTOR` and `SATURATION_FACTOR` from config if unused
- [ ] `enhance()` method signature unchanged — drop-in replacement
- [ ] Order: CLAHE → saturation curve → edge-aware sharpening

## Test Plan

### Unit Tests

| Test | AC |
|------|----|
| `test_clahe_improves_local_contrast` | AC2.5 — measure local variance of L channel before/after |
| `test_clahe_preserves_dimensions` | AC2.5 — output same size as input |
| `test_saturation_curve_boosts_midrange` | AC2.5 — mid-S pixels increase more than high-S pixels |
| `test_saturation_preserves_range` | AC2.5 — no pixel values outside [0, 255] |
| `test_edge_sharpening_increases_detail` | AC2.5 — Laplacian variance (focus measure) increases |
| `test_edge_sharpening_no_noise_amplification` | AC2.5 — flat region std dev doesn't increase significantly |
| `test_enhancement_returns_rgb` | AC2.5 — output is RGB mode (unchanged from Phase 1) |
| `test_enhancement_preserves_dimensions` | AC2.5 — output same dimensions (unchanged from Phase 1) |

### Integration Tests

| Test | Description |
|------|----|
| `test_before_after_endpoint` | Process image, fetch both preview URLs, verify they're different |
| `test_full_pipeline_with_new_enhancement` | Upload → crop → process → PDF downloads OK |

### Top 3 Given/When/Then

1. **Given** a low-contrast image, **When** enhanced with CLAHE, **Then** the mean local variance of the L channel increases by at least 20%.
2. **Given** an image with S-channel values clustered around 128, **When** saturation curve applied with boost=0.4, **Then** mean S increases and max S ≤ 255.
3. **Given** a processed image, **When** before/after toggle clicked, **Then** preview swaps to the original crop image (no enhancement, no grid).
