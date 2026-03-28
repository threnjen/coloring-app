# Mosaic Coloring App — Phases Overview

## Project Summary

A web application that converts uploaded photos into mosaic color-by-number coloring sheets. Users upload a photo, crop/edit it, and the app quantizes colors and generates a numbered grid (square pixels or packed circles) suitable for printing on US Letter paper. Sheets can be saved as PDF, emailed, or assembled into a spiral-bound book via print-on-demand.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.12+ / FastAPI | API server, static file serving, image processing |
| Frontend | Vanilla HTML/JS/CSS | No build step; Cropper.js for crop interaction |
| Image Processing | Pillow, OpenCV, scikit-learn | Enhancement, quantization (K-means in LAB), grid rendering |
| Background Removal | rembg | Subject cutout (Phase 3) |
| PDF Generation | ReportLab | Precise grid + legend layout on US Letter |
| Print-on-Demand | Lulu API | Book ordering (Phase 5) |

## Grid Specifications

- **Paper**: US Letter (215.9mm × 279.4mm)
- **Ground truth**: 50 columns at 4mm = 200mm width; ~8mm side margins
- **Printable area**: 200mm × 263.5mm
- **Color count**: 8–20 colors
- **Labels**: Single character — `0–9` then `A–J` (no two-digit labels)
- **Legend**: Separate page (or on back of previous sheet in book layout)

| Component Size | Columns × Rows | Total Cells |
|----------------|---------------|-------------|
| 3mm | 60 × 80 | ~4,800 |
| 4mm | 50 × 65 | ~3,250 |
| 5mm | 40 × 52 | ~2,080 |
| 6mm | 33 × 43 | ~1,419 |

## Phase Table

| Phase | Name | Status | Dependencies | Deliverables |
|-------|------|--------|-------------|-------------- |
| 1 | Core Pipeline POC | Not Started | None | Upload, crop, enhance, quantize, square grid, preview, PDF download |
| 2 | Mosaic Modes & Color Refinement | Not Started | Phase 1 | Circle mosaic, size selector, advanced enhancement, palette editing |
| 3 | Image Editing Tools | Not Started | Phase 1 | Subject cutout, preset/custom backgrounds, compositing |
| 4 | Export, Sharing & Persistence | Not Started | Phase 1 | Email PDF, save/load projects, multi-sheet management |
| 5 | Print-on-Demand Integration | Not Started | Phase 4 | Lulu API, book assembly, order flow |

## Dependency Graph

```
Phase 1 (Core Pipeline)
  ├── Phase 2 (Mosaic Modes) — extends rendering + enhancement
  ├── Phase 3 (Image Editing) — adds pre-processing before quantization
  └── Phase 4 (Export & Persistence) — adds output/sharing features
        └── Phase 5 (Print-on-Demand) — requires multi-sheet persistence
```

Phases 2, 3, and 4 can be developed in parallel after Phase 1. Phase 5 requires Phase 4.

## Non-Goals

- Mobile native app (web only, all phases)
- User accounts or authentication
- Paper sizes other than US Letter
- Real-time collaboration
- E-commerce beyond Lulu integration
