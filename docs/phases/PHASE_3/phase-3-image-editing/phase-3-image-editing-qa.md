# QA Skeleton: Phase 3 — Image Editing Tools

**Date:** 2026-03-28
**Mode:** Pre-Implementation QA Skeleton
**Scope:** Background removal (cutout), preset/custom background selection, subject positioning/scaling, composite preview, two-level undo, skip-editing flow
**Status:** Draft — to be expanded into a Release QA Plan after implementation

## References

- Plan: `phase-3-image-editing-plan.md`
- Context: `phase-3-image-editing-context.md`
- Tasks: `phase-3-image-editing-tasks.md`

---

## Planned Feature Summary

Phase 3 adds an image editing step between crop and mosaic processing. Users can remove the background from their cropped image (cutout), choose a preset or custom background, position and scale the subject on the new background, preview the composite, and proceed to the existing quantize → grid → PDF pipeline. A two-level undo allows reverting the composite (back to cutout + picker) or the cutout entirely (back to original crop). Users can also skip editing altogether, preserving the Phase 1 flow.

---

## Anticipated Manual QA Areas

### QA1: Cutout Activation & Visual Quality

**Acceptance Criteria:** AC3.1, AC3.2, AC3.9
**Why manual QA:** Visual quality of mask edges, checkerboard transparency rendering, and subjective quality across varied subjects cannot be fully verified by automated pixel checks.

- [ ] **Trigger cutout on a photo of a person** — Upload a photo with a clear human subject, crop it, click "Cut Out Subject." **Expected:** Subject is isolated; checkerboard transparency pattern visible behind subject; mask edges look clean and smooth with no jagged aliasing
- [ ] **Trigger cutout on a pet photo** — Upload a photo of a pet (fur edges). **Expected:** Subject isolated; fur edges are reasonably smooth, feathered rather than hard-cut
- [ ] **Trigger cutout on a simple object** — Upload a photo of an everyday object on a plain background. **Expected:** Clean cutout with accurate outline
- [ ] **Trigger cutout on a complex/ambiguous subject** — Upload a photo with no clear foreground subject or low contrast between subject and background. **Expected:** Cutout completes without error; user can evaluate mask quality and use "Undo Cutout" if unsatisfactory
- [ ] **First-time model download indicator** — If rembg model has not been downloaded yet, trigger cutout. **Expected:** Loading indicator "Downloading AI model (first time only)..." is displayed during download; cutout completes after download

### QA2: Preset Background Picker

**Acceptance Criteria:** AC3.3
**Why manual QA:** Visual rendering of thumbnail grid, color accuracy of solids/gradients, and selection interaction are UI behaviors.

- [ ] **View preset background list** — After cutout, observe the background picker panel. **Expected:** Thumbnail grid shows all programmatic backgrounds (solids: white, light gray, sky blue, pale yellow, mint green, light pink; gradients: blue-to-white, sunset, forest)
- [ ] **Select a solid preset** — Click a solid color thumbnail (e.g., sky blue). **Expected:** Background behind subject changes to selected solid color in preview
- [ ] **Select a gradient preset** — Click a gradient thumbnail (e.g., sunset). **Expected:** Background behind subject changes to the gradient in preview
- [ ] **Switch between presets** — Click multiple different thumbnails in sequence. **Expected:** Preview updates each time to reflect newly selected background
- [ ] **File-based presets appear if present** — Place a valid image file in `static/presets/`, reload the app. **Expected:** File-based preset appears in the thumbnail list alongside programmatic backgrounds

### QA3: Custom Background Upload

**Acceptance Criteria:** AC3.4
**Why manual QA:** File upload UI interaction, validation error display, and visual result of custom background behind subject.

- [ ] **Upload a valid custom background** — After cutout, use the custom background upload input to select a JPEG/PNG image. **Expected:** Custom image appears behind the subject in preview
- [ ] **Upload a small custom background** — Upload an image smaller than the crop dimensions. **Expected:** Background scaled to fill (no empty areas visible); subject composited correctly
- [ ] **Upload a large custom background** — Upload an image much larger than the crop dimensions. **Expected:** Background center-cropped to match crop dimensions; no stretching or distortion
- [ ] **Upload an invalid file** — Attempt to upload a non-image file (e.g., .txt). **Expected:** Validation error message displayed; no crash or broken state

### QA4: Position & Scale

**Acceptance Criteria:** AC3.5
**Why manual QA:** Drag interaction smoothness, visual feedback during drag, and scale slider responsiveness are inherently UI behaviors.

- [ ] **Drag subject to reposition** — After cutout with a background selected, click and drag the subject. **Expected:** Subject follows the pointer smoothly; position updates in real-time
- [ ] **Adjust scale slider** — Move the scale slider from default (1.0) to a smaller value (e.g., 0.5) and a larger value (e.g., 1.5). **Expected:** Subject visually shrinks and grows accordingly
- [ ] **Scale to minimum (0.25)** — Set slider to minimum. **Expected:** Subject renders at 25% of original size
- [ ] **Scale to maximum (2.0)** — Set slider to maximum. **Expected:** Subject renders at 200% of original size
- [ ] **Subject overflow with large scale** — Scale up and drag subject partially off-canvas. **Expected:** Subject clipped at canvas edge; warning displayed if >30% of subject is clipped
- [ ] **Position after scale change** — Scale the subject, then drag to reposition. **Expected:** Drag works correctly at the new scale; no jumps or offset errors

### QA5: Composite Preview & Continue to Pipeline

**Acceptance Criteria:** AC3.6, AC3.7
**Why manual QA:** End-to-end visual flow from composite preview through mosaic PDF generation crosses multiple systems.

- [ ] **Apply composite and preview** — After positioning subject on background, click "Apply Composite." **Expected:** Composite preview renders in-place showing final result before proceeding
- [ ] **Continue to processing** — After applying composite, click "Continue." **Expected:** Processing step starts; quantization and grid generation work on the composite image
- [ ] **Full pipeline: composite to PDF** — Complete the full flow: upload → crop → cutout → background → position → apply → continue → process → download PDF. **Expected:** PDF downloads successfully; mosaic is generated from the composite image, not the original crop
- [ ] **Composite dimensions match crop** — After compositing, proceed to process. **Expected:** No dimension mismatch errors; output dimensions consistent with original crop

### QA6: Undo Composite

**Acceptance Criteria:** AC3.8a
**Why manual QA:** State management and UI transitions after undo are interaction behaviors.

- [ ] **Undo after applying composite** — Apply a composite, then click "Undo Composite." **Expected:** Returns to cutout + background picker state; subject cutout still visible; can select a different background
- [ ] **Re-composite after undo** — Undo composite, select a different background, reposition, and apply again. **Expected:** New composite applies correctly; no artifacts from previous composite

### QA7: Undo Cutout

**Acceptance Criteria:** AC3.8b
**Why manual QA:** Full editor state reset and UI transition back to crop result.

- [ ] **Undo cutout after cutting** — After performing cutout (before or after compositing), click "Undo Cutout." **Expected:** Returns to original cropped image; editor panel is hidden; background picker and position controls are not visible
- [ ] **Re-enter editing after undo cutout** — Undo cutout, then click "Cut Out Subject" again. **Expected:** Cutout re-runs; editor returns to cutout state with fresh background picker

### QA8: Skip Editing (Phase 1 Flow Preserved)

**Acceptance Criteria:** AC3.7 (pipeline compatibility)
**Why manual QA:** Ensures existing Phase 1 user flow is not broken by the new editor step insertion.

- [ ] **Skip editing entirely** — Upload → crop → click "Skip" in the editor step. **Expected:** Process step appears directly; mosaic generates from the cropped image (Phase 1 behavior unchanged)
- [ ] **Full skip pipeline to PDF** — Upload → crop → skip → process → download PDF. **Expected:** PDF downloads successfully; identical behavior to Phase 1 flow

---

## Anticipated Cross-Cutting Concerns

- [ ] **Performance — rembg inference time** — Observe how long cutout takes on reasonably sized images (e.g., 1000×1000, 3000×3000). **Expected:** Completes within a reasonable time; UI is not frozen (async processing)
- [ ] **Performance — composite responsiveness** — Apply composite with various background types and positions. **Expected:** Composite completes quickly; no noticeable lag
- [ ] **Security — custom upload validation** — Attempt uploading oversized files, non-image files, and files with manipulated extensions. **Expected:** All rejected with clear error messages; no server errors
- [ ] **Security — preset filename safety** — Place a file with path-traversal characters (e.g., `../evil.png`) in `static/presets/`. **Expected:** File is rejected/ignored by the background provider
- [ ] **Accessibility — keyboard navigation** — Navigate the editor controls (cutout button, background thumbnails, scale slider, undo buttons) using keyboard only. **Expected:** All controls are reachable and operable via keyboard
- [ ] **Accessibility — scale slider** — Use keyboard arrows to adjust the scale slider. **Expected:** Slider value changes in increments; subject updates accordingly
- [ ] **App restart/reset** — After completing or partially completing the editing flow, click the app's restart/reset button. **Expected:** Editor state is fully cleared; app returns to initial upload state

---

## Open Questions

- What is the acceptable rembg inference time threshold for various image sizes?
- Will file-based presets be shipped with the app, or is the directory always initially empty?
- Should the editor step be shown even if the user never wants to edit (skip always visible)?
- Are there specific accessibility requirements beyond basic keyboard navigation (e.g., screen reader announcements for cutout completion)?
