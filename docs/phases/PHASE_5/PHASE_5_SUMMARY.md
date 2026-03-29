# Phase 5: Print-on-Demand Integration

**Status**: Not Started
**Dependencies**: Phase 4 (Export, Sharing & Persistence)
**Cross-references**: [PHASES_OVERVIEW.md](PHASES_OVERVIEW.md) | [PHASE_4_EXPORT_SHARING.md](PHASE_4_EXPORT_SHARING.md)

---

## Goal

Integrate with the Lulu print-on-demand API so users with 20+ saved sheets can order a spiral-bound coloring book. The app assembles the book (cover, coloring sheets with legends on the backs of preceding pages), sends it to Lulu, and lets the user complete the order.

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC5.1 | User with 20+ saved sheets sees an "Order Book" option |
| AC5.2 | User can select which sheets to include in the book (minimum 20) |
| AC5.3 | User can arrange the sheet order via drag-and-drop |
| AC5.4 | App generates a print-ready PDF book: cover page, then alternating legend (back of previous page) and coloring sheet pages |
| AC5.5 | First coloring sheet has no preceding legend (or a title/intro page on its back) |
| AC5.6 | Book PDF meets Lulu's print specifications (bleed, margins, color space, resolution) |
| AC5.7 | User can preview the assembled book layout before ordering |
| AC5.8 | App submits the book to Lulu via their API and returns a checkout/payment URL |
| AC5.9 | User is redirected to Lulu to complete payment |
| AC5.10 | App can query and display order status from Lulu |

## Architecture Changes

### New/Modified Files

| File | Change |
|------|--------|
| `src/book/` | New directory |
| `src/book/assembly.py` | Book PDF assembly: cover, page ordering (legend on verso, grid on recto) |
| `src/book/cover.py` | Cover page generation (title, optional image collage) |
| `src/book/lulu.py` | Lulu API client: create print job, upload interior/cover, get pricing, submit order, check status |
| `src/book/specs.py` | Lulu print specs: paper size, bleed, margins, color profile, DPI requirements |
| `src/api/routes.py` | New endpoints for book assembly, Lulu order flow |
| `src/api/schemas.py` | Add `BookRequest`, `BookPreview`, `OrderStatus` models |
| `src/config.py` | Add Lulu API credentials, book defaults |
| `static/js/book.js` | New — sheet selector, drag-to-reorder, book preview, order button |
| `static/css/style.css` | Styles for book builder UI |

### API Endpoints (New)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/book/preview` | Accept sheet IDs + order; return book layout preview (page list with thumbnails) |
| POST | `/api/book/assemble` | Generate the full print-ready PDF |
| GET | `/api/book/assemble/{book_id}` | Download the assembled book PDF (for user review) |
| POST | `/api/book/order` | Submit to Lulu; return checkout URL |
| GET | `/api/book/order/{order_id}/status` | Query Lulu for order status |

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

Key Lulu API operations:
1. **Create Print Job** — specify product (spiral-bound, US Letter, color interior)
2. **Upload Interior PDF** — the assembled book content
3. **Upload Cover PDF** — front/back/spine cover file per Lulu's template
4. **Calculate Cost** — get printing + shipping cost for quoting to user
5. **Create Order** — finalize; Lulu returns a payment URL
6. **Check Status** — poll for production/shipping status

Lulu product specifications (to verify during implementation):
- Binding: Coil/spiral bound
- Interior: US Letter (8.5" × 11"), color
- Paper: Standard color (70# or 80# text)
- Cover: Soft cover, color

### Cover Generation

- Title: user-provided book title (default: "My Coloring Book")
- Optional: collage of preview thumbnails from included sheets
- Must meet Lulu cover template requirements (bleed, spine width based on page count)

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Exactly 20 sheets selected | Minimum met; allow order |
| Fewer than 20 sheets | "Order Book" disabled; show "Need X more sheets" message |
| Odd total page count | Lulu may require even page count — add blank page if needed |
| Lulu API downtime | Graceful error: "Ordering temporarily unavailable, try again later" |
| Lulu API credentials not configured | Hide "Order Book" entirely; log warning at startup |
| Very large book (100+ sheets) | Check Lulu's max page count limit; warn if exceeded |
| Sheet uses features from Phase 2/3 | Book assembly works regardless — it uses the saved grid data and palette |
| User modifies a sheet after book preview | Warn that book must be re-assembled |
| Lulu product/API changes | Isolate all Lulu specifics in `lulu.py` and `specs.py` for easy updates |

## Security Considerations

- **Lulu API key**: Stored as environment variable, never exposed to frontend
- **Payment**: User redirected to Lulu's own checkout — app never handles payment data
- **Order data**: Store order ID and status locally; no sensitive payment info persisted
- **Rate limiting**: Limit book assembly requests (CPU-intensive PDF generation)

## Observability

- Log book assembly: sheet count, page count, PDF file size, generation time
- Log all Lulu API calls: endpoint, response status, latency
- Log order lifecycle: created, submitted, payment URL generated, status checks
- Alert-worthy: Lulu API errors, assembly failures, books with unusually high page counts

## Test Plan

### Unit Tests

| Test | Maps to |
|------|---------|
| `test_book_page_count` | AC5.4 — N sheets produces 2N+1 interior pages |
| `test_book_page_order` | AC5.4 — alternating legend/grid pattern correct |
| `test_first_page_is_title` | AC5.5 — page 1 is title, not a legend |
| `test_cover_meets_specs` | AC5.6 — cover dimensions match Lulu template for page count |
| `test_interior_meets_specs` | AC5.6 — interior page size, bleed, DPI correct |
| `test_minimum_20_sheets` | AC5.1 — order blocked with fewer than 20 |
| `test_sheet_reorder` | AC5.3 — changing order changes page sequence |
| `test_even_page_count_padding` | Edge case — blank page added if needed |

### Integration Tests (Lulu API mocked)

| Test | Description |
|------|-------------|
| `test_book_assembly_end_to_end` | 20 saved sheets → assemble → verify PDF page count and structure |
| `test_lulu_order_flow` | Assemble → submit (mocked) → verify API called with correct payload → checkout URL returned |
| `test_lulu_status_check` | Submit order (mocked) → check status → verify status returned correctly |
| `test_lulu_api_error_handling` | Simulate Lulu 500 → verify graceful error message to user |

### Top 5 High-Value Test Cases

1. **Given** 25 saved sheets, **When** user selects 22, reorders them, and assembles, **Then** the book PDF has 45 pages (1 title + 22 legends + 22 grids) in the correct alternating order.

2. **Given** an assembled book PDF, **When** inspected, **Then** page dimensions match Lulu's US Letter spec with correct bleed, and interior resolution is >= 300 DPI.

3. **Given** an assembled book, **When** submitted to Lulu (mocked), **Then** the API receives the correct product type (spiral-bound, color, US Letter) and returns a checkout URL.

4. **Given** a user with 15 sheets, **When** they view the sheet list, **Then** "Order Book" is disabled with a message "Need 5 more sheets to order a book."

5. **Given** Lulu API returns a 503 error, **When** user tries to submit an order, **Then** the app shows "Ordering temporarily unavailable" and does not crash or leave orphaned state.

## QA Manual Test Scenarios

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| QA1 | Book eligibility | Save 20+ sheets | "Order Book" button becomes active |
| QA2 | Sheet selection | Click "Order Book"; select/deselect sheets | Selected count updates; minimum 20 enforced |
| QA3 | Reorder sheets | Drag sheets to rearrange order | Order updates; preview reflects new sequence |
| QA4 | Book preview | After selecting and ordering sheets, view preview | Page-by-page preview showing title, legend/grid alternation |
| QA5 | Assemble PDF | Click "Assemble Book" | PDF generated; available for download and review |
| QA6 | Order submission | Click "Order" after assembly | Redirected to Lulu checkout page |
| QA7 | Order status | After ordering, view order status | Current status displayed (processing, shipped, etc.) |
| QA8 | Under minimum | With < 20 sheets, check "Order Book" | Button disabled; message shows how many more sheets needed |
