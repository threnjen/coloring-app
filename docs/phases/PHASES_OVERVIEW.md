# Mosaic Coloring App — Phases Overview

## Project Summary

A web application that converts uploaded photos into mosaic color-by-number coloring sheets. Users upload a photo, crop/edit it, and the app quantizes colors and generates a numbered grid (square pixels or packed circles) suitable for printing on US Letter paper. Sheets can be saved as PDF or assembled into a spiral-bound book via print-on-demand. Hosted on AWS with social login (Google, Facebook, Apple) and per-user sheet persistence.

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.12+ / FastAPI | API server, image processing |
| Frontend | Vanilla HTML/JS/CSS | No build step; Cropper.js for crop interaction |
| Image Processing | Pillow, OpenCV, scikit-learn | Enhancement, quantization (K-means in LAB), grid rendering |
| Background Removal | rembg | Subject cutout (Phase 3) |
| PDF Generation | ReportLab | Precise grid + legend layout on US Letter |
| Auth | AWS Cognito | Social login federation (Google, Facebook, Apple) |
| Database | AWS RDS PostgreSQL | User data, sheet metadata, mosaic state |
| Object Storage | AWS S3 | Generated PDFs, preview PNGs, grid data |
| Content Safety | Amazon Rekognition | Moderation of uploaded images |
| Compute | AWS ECS Fargate | Containerized deployment, auto-scaling |
| CDN | AWS CloudFront | Static asset serving, HTTPS termination |
| Print-on-Demand | Lulu API | Book ordering (Phase 6) |

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
| 4 | AWS Deployment, Auth & Content Safety | Not Started | Phase 1 | Dockerized Fargate deploy, Cognito social login, Rekognition moderation, CloudFront |
| 5 | User Persistence & Sheet Management | Not Started | Phase 4 | RDS + S3 persistence, sheet CRUD, user library, data lifecycle |
| 6 | Print-on-Demand Integration | Not Started | Phase 5 | Lulu API, book assembly, order flow |

## Dependency Graph

```
Phase 1 (Core Pipeline)
  ├── Phase 2 (Mosaic Modes) — extends rendering + enhancement
  ├── Phase 3 (Image Editing) — adds pre-processing before quantization
  └── Phase 4 (AWS Deploy, Auth & Content Safety) — platform shift to AWS
        └── Phase 5 (User Persistence & Sheet Management) — RDS + S3 persistence
              └── Phase 6 (Print-on-Demand) — requires multi-sheet persistence
```

Phases 2, 3, and 4 can be developed in parallel after Phase 1. Phase 5 requires Phase 4. Phase 6 requires Phase 5.

## Infrastructure Cost Estimate (Monthly Baseline)

| Service | Est. Cost | Notes |
|---------|-----------|-------|
| ECS Fargate (1 task, 1 vCPU, 4GB) | ~$45 | Auto-scales with traffic |
| ALB | ~$16 | HTTPS termination, health checks |
| RDS db.t4g.micro (PostgreSQL) | ~$12 | Free-tier eligible first 12 months |
| S3 | ~$1 | Generated PDFs, previews, grid data |
| Cognito | $0 | Free up to 50K MAU |
| Rekognition | ~$1–5 | Scales with upload volume |
| CloudFront | ~$0 | Free tier covers low-moderate traffic |
| Route 53 | $0.50 | When domain is registered |
| **Total** | **~$75–80/mo** | Mostly fixed at low usage |

## Constraints & Non-Goals

- Mobile native app (web only, all phases)
- Paper sizes other than US Letter
- Real-time collaboration
- E-commerce beyond Lulu integration
- Email PDF delivery (removed — may revisit later)
- Storing original uploaded images long-term (deleted after processing for content safety)

## Architecture Notes

- **Compute**: ECS Fargate chosen over EC2 for zero instance management. 1 vCPU / 4GB minimum per task due to rembg/OpenCV memory requirements. Can shift to ECS on EC2 if cost pressure demands it — Docker image and task definition remain the same.
- **Auth**: Cognito with social IdP federation (Google, Facebook, Apple) via Hosted UI. No username/password — social login only. FastAPI validates Cognito JWTs. Users identified by Cognito `sub` UUID in RDS.
- **Content Safety**: Amazon Rekognition `DetectModerationLabels` scans every uploaded image before processing. Flagged content rejected immediately. Original images deleted after mosaic generation regardless of moderation result.
- **Storage**: S3 for generated artifacts (PDFs, previews, grid data). RDS PostgreSQL for user records, sheet metadata, and mosaic configuration state (JSON columns). No original images persisted.
- **Networking**: ALB in public subnets, Fargate tasks + RDS in private subnets. CloudFront serves static frontend assets. ACM for free SSL.
