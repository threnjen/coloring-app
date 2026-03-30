# Phase 6: Print-on-Demand Integration

**Status**: Planned
**Depends on**: Phase 5 (User Persistence & Sheet Management)
**Estimated complexity**: Large
**Cross-references**: [PHASES_OVERVIEW.md](../PHASES_OVERVIEW.md) | [PHASE_5_SUMMARY.md](../PHASE_5/PHASE_5_SUMMARY.md)

## Objective

Integrate with the Lulu print-on-demand API so users with 20+ saved sheets can order a spiral-bound coloring book. The app assembles the book (cover, coloring sheets with legends on the backs of preceding pages), sends it to Lulu, and lets the user complete the order. Built on the RDS + S3 persistence layer from Phase 5.

## Scope

### In Scope
- Book assembly engine: generate a print-ready PDF from selected sheets (cover, alternating legend/grid pages)
- Lulu API client: create print job, upload files, calculate cost, submit order, check status
- Book builder UI: sheet selector, drag-to-reorder, book preview, order button
- Cover generation: title page, optional collage of sheet previews
- Order tracking: store order metadata in RDS, query Lulu for status updates
- Assembled book PDF stored in S3

### Out of Scope
- Payment processing (users redirected to Lulu's checkout — app never handles payment)
- Binding types other than spiral-bound
- Paper sizes other than US Letter
- Multiple print-on-demand providers
- Sharing books between users

## Key Deliverables

| # | Deliverable | Description | Likely Features |
|---|-------------|-------------|-----------------|
| 1 | Book assembly engine | PDF generation: cover + alternating legend/grid interior pages | ReportLab, page layout |
| 2 | Lulu API client | Create print job, upload interior/cover, pricing, order, status | HTTP client, API integration |
| 3 | Cover generator | Title page, preview collage, Lulu cover template compliance | ReportLab, image compositing |
| 4 | Book builder UI | Sheet selector, drag-to-reorder, preview, order flow | Vanilla JS, CSS |
| 5 | Order management | RDS schema for orders, status tracking, order history | Database, Lulu polling |

## Technical Context

Phase 5 provides the persistence layer this phase builds on:
- `users` and `sheets` tables in RDS PostgreSQL
- Sheet assets (preview PNGs, grid data, PDFs) in S3 under per-user prefixes
- Authenticated CRUD API with user-scoped access
- `MosaicSheet` model with serialization to JSONB + S3

This phase adds:
- `books` and `book_orders` tables in RDS
- Assembled book PDFs in S3
- Lulu API integration as an isolated client module

### Book Page Layout

For a book with N coloring sheets, the interior pages are:

| Page # | Content | Side |
|--------|---------|------|
| 1 | Title / intro page | Recto (right) |
| 2 | Legend for Sheet 1 | Verso (left / back of page 1) |
| 3 | Sheet 1 grid | Recto (right) |
| 4 | Legend for Sheet 2 | Verso (left / back of sheet 1) |
| 5 | Sheet 2 grid | Recto |
| ... | ... | ... |
| 2N | Legend for Sheet N | Verso |
| 2N+1 | Sheet N grid | Recto |

Total interior pages: `2N + 1` (title + N legends + N grids).

### Lulu API Integration

Key operations:
1. **Create Print Job** — specify product (spiral-bound, US Letter, color interior)
2. **Upload Interior PDF** — the assembled book content from S3
3. **Upload Cover PDF** — front/back/spine cover file per Lulu's template
4. **Calculate Cost** — get printing + shipping cost for quoting to user
5. **Create Order** — finalize; Lulu returns a payment URL
6. **Check Status** — poll for production/shipping status

Lulu product specifications (to verify during implementation):
- Binding: Coil/spiral bound
- Interior: US Letter (8.5" × 11"), color
- Paper: Standard color (70# or 80# text)
- Cover: Soft cover, color

### Database Schema Additions (Conceptual)

- `books` — `id (UUID PK)`, `user_id (FK → users)`, `title`, `created_at`, `sheet_ids (UUID[])`, `sheet_order (UUID[])`, `page_count`, `s3_interior_key`, `s3_cover_key`, `status`
- `book_orders` — `id (UUID PK)`, `book_id (FK → books)`, `lulu_order_id`, `lulu_checkout_url`, `status`, `created_at`, `updated_at`, `cost_cents`

### S3 Object Layout Addition

```
s3://{bucket}/{user_id}/
  └── books/
      └── {book_id}/
          ├── interior.pdf    # Assembled interior PDF
          └── cover.pdf       # Cover PDF per Lulu template
```

## Dependencies & Risks

- **Dependency**: Phase 5 complete — RDS + S3 persistence working, sheet library functional
- **Dependency**: Lulu API developer account and credentials
- **Risk**: Lulu API may change or have undocumented requirements. **Mitigation**: Isolate all Lulu specifics in dedicated client module; test against sandbox/staging API first.
- **Risk**: Book assembly is CPU-intensive (generating large multi-page PDFs). **Mitigation**: Rate limit assembly requests per user; generate asynchronously with status polling; consider dedicated task queue if needed.
- **Risk**: Lulu may require even page counts or specific bleed/margin specs not yet known. **Mitigation**: Research specs from Lulu docs during implementation; add blank pages if needed for even count.
- **Risk**: User modifies a sheet after book assembly. **Mitigation**: Track sheet `updated_at` vs book `created_at`; warn user to re-assemble if sheets changed.

## Success Criteria

- [ ] User with 20+ saved sheets sees an "Order Book" option
- [ ] User can select which sheets to include (minimum 20) and arrange order via drag-and-drop
- [ ] App generates a print-ready PDF book with correct page layout (title, alternating legend/grid)
- [ ] Book PDF meets Lulu's print specifications (bleed, margins, color space, resolution)
- [ ] User can preview the assembled book layout before ordering
- [ ] App submits the book to Lulu and returns a checkout/payment URL
- [ ] User is redirected to Lulu to complete payment
- [ ] App can query and display order status from Lulu
- [ ] Assembled PDFs stored in S3 under user's prefix
- [ ] Order metadata persisted in RDS; survives app restarts

## QA Considerations

- This phase includes significant frontend/UI changes (book builder, drag-to-reorder, preview) requiring manual QA docs
- Lulu checkout redirect must be tested in real browser flow (mocked in automated tests, manual verification against Lulu sandbox)
- Book assembly output requires visual inspection — automated tests verify structure/page count, but print quality needs manual review
- Mobile browser testing for drag-to-reorder UX

## Notes for Feature - Decomposer

Suggested feature boundaries:
1. **Book assembly engine** — PDF generation logic: cover page, page ordering (legend on verso, grid on recto), blank page padding. Pure computation — no Lulu dependency. Can be tested with mocked sheet data.
2. **Cover generator** — Title page and optional preview collage. Separate from interior assembly. Must comply with Lulu cover template (spine width varies with page count).
3. **Lulu API client** — Isolated HTTP client: create job, upload files, pricing, order, status. All Lulu-specific logic in one module. Developed against Lulu sandbox API. No frontend dependency.
4. **Book builder UI** — Sheet selector, drag-to-reorder, preview display, order button, status display. Depends on assembly and Lulu client APIs.
5. **Order management** — RDS schema for books and orders, status tracking, order history view. Connects Lulu client responses to persistent storage.

Key integration point: Book assembly reads sheet data from Phase 5's persistence layer (grid data from S3, palette from RDS). The Feature - Decomposer should ensure the assembly engine takes serialized sheet data as input, not live `MosaicSheet` objects — keeping it decoupled from the processing pipeline.
