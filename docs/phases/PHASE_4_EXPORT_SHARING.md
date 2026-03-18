# Phase 4: Export, Sharing & Persistence

**Status**: Not Started
**Dependencies**: Phase 1 (Core Pipeline POC)
**Cross-references**: [PHASES_OVERVIEW.md](PHASES_OVERVIEW.md) | [PHASE_1_CORE_PIPELINE.md](PHASE_1_CORE_PIPELINE.md)

---

## Goal

Add email PDF delivery, project save/load, and multi-sheet session management. After this phase, users can build a collection of coloring sheets, retrieve previous work, and share sheets via email. This phase also establishes the persistence layer required by Phase 5 (print-on-demand).

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC4.1 | User can enter an email address and send a PDF of the current sheet as an attachment |
| AC4.2 | Email is sent via a transactional email service with proper deliverability (not raw SMTP) |
| AC4.3 | User can save a completed mosaic sheet with a name/title |
| AC4.4 | User can view a list of all saved sheets in the current session |
| AC4.5 | User can load a previously saved sheet and view/re-edit it |
| AC4.6 | User can delete a saved sheet |
| AC4.7 | User can manage multiple sheets — create new ones without losing saved work |
| AC4.8 | Saved sheet data persists across browser refreshes (server-side storage) |
| AC4.9 | Each saved sheet stores: original image, crop coordinates, editing state (cutout/composite if used), color palette (including edits), mosaic mode, component size, grid data |
| AC4.10 | Sheet count is displayed; user can see when they have 20+ sheets (relevant for Phase 5) |

## Architecture Changes

### New/Modified Files

| File | Change |
|------|--------|
| `src/persistence/` | New directory |
| `src/persistence/storage.py` | SQLite-backed storage for sessions and sheets |
| `src/persistence/models.py` | SQLAlchemy or raw SQLite models: Session, Sheet |
| `src/api/routes.py` | New endpoints for save/load/delete/list sheets, send email |
| `src/api/schemas.py` | Add `SheetSave`, `SheetSummary`, `EmailRequest` models |
| `src/email/sender.py` | New — email sending via transactional service |
| `src/config.py` | Add email config, SQLite path, session TTL |
| `static/js/app.js` | Sheet management panel: save, list, load, delete, email dialog |
| `static/css/style.css` | Styles for sheet list, save dialog, email form |

### Persistence Design

**SQLite** — single file, zero-config, sufficient for single-user local use and small-scale deployment.

Tables:
- `sessions` — `id (UUID)`, `created_at`, `last_accessed`
- `sheets` — `id (UUID)`, `session_id (FK)`, `title`, `created_at`, `updated_at`, `original_image_path`, `crop_coords (JSON)`, `editing_state (JSON)`, `palette (JSON)`, `mosaic_mode`, `component_size`, `grid_data_path`

Session identified by a cookie (UUID). No authentication — sessions are anonymous.

Image files and grid data stored on filesystem; database stores metadata and paths.

### Email Service

**Recommended**: Resend, Postmark, or SendGrid — all have free tiers suitable for POC, Python SDKs, and reliable deliverability.

- Configurable via environment variable (`EMAIL_PROVIDER`, `EMAIL_API_KEY`)
- Email contains: subject line with sheet title, brief body text, PDF attached
- Rate limit: max 5 emails per session per hour (prevent abuse)
- Sender address: configurable (requires domain verification with chosen provider)

### API Endpoints (New)

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/sheets` | Save current mosaic as a named sheet |
| GET | `/api/sheets` | List all sheets in current session |
| GET | `/api/sheets/{sheet_id}` | Load a saved sheet (full state) |
| DELETE | `/api/sheets/{sheet_id}` | Delete a saved sheet |
| POST | `/api/sheets/{sheet_id}/email` | Email the sheet's PDF to a given address |

### User Flow

```
[Existing pipeline produces a mosaic]
  → "Save Sheet" → enter title → sheet saved to session
  → "My Sheets" → see list of saved sheets with thumbnails
  → Click a sheet → loads full state, can re-edit or re-download
  → "Email PDF" → enter email address → PDF sent
  → "New Sheet" → start fresh upload; saved sheets preserved
  → Badge shows "3 sheets saved" / "20+ sheets — order a book!"
```

## Correctness & Edge Cases

| Scenario | Handling |
|----------|----------|
| Session cookie lost (cleared browser) | Session is gone — no recovery without auth. Accept this for now. |
| Save sheet with no title | Default to "Untitled Sheet" + timestamp |
| Duplicate title | Allow — sheets identified by UUID, not title |
| Load sheet after source image deleted (temp cleanup) | Store original image permanently on save (copy from temp to persistent storage) |
| Email to invalid address | Validate format client-side; rely on email provider for bounce handling |
| Email provider not configured | Disable email button; show "Email not configured" message |
| Delete sheet that's currently being viewed | Clear editor and return to sheet list |
| Large number of sheets (50+) | Paginate sheet list; consider storage limits |

## Security Considerations

- **Email**: Validate email format; rate limit sending; never expose API key to frontend
- **Session**: Cookie is `HttpOnly`, `SameSite=Lax`; session UUID is cryptographically random
- **File storage**: Saved images stored under session-specific directories; no cross-session access
- **Input validation**: Sheet titles sanitized (strip HTML/script); max length enforced
- **SQLite**: Parameterized queries only — no string interpolation in SQL

## Observability

- Log email send attempts (success/failure, recipient domain, sheet ID) — never log full email address
- Log sheet save/load/delete operations with session ID and sheet ID
- Track session sheet count for monitoring
- Log storage usage per session

## Test Plan

### Unit Tests

| Test | Maps to |
|------|---------|
| `test_save_sheet_persists` | AC4.3, AC4.8 — save and reload returns same data |
| `test_list_sheets_returns_session_only` | AC4.4 — only returns sheets for current session |
| `test_load_sheet_restores_full_state` | AC4.5, AC4.9 — all fields restored including palette edits |
| `test_delete_sheet_removes_data` | AC4.6 — sheet no longer in list; files cleaned up |
| `test_email_validates_address` | AC4.1 — rejects clearly invalid addresses |
| `test_email_rate_limit` | AC4.2 — blocks after 5 emails per hour |
| `test_sheet_count_accurate` | AC4.10 — count matches actual saved sheets |
| `test_save_copies_image_from_temp` | AC4.9 — original image persisted, not just temp path |

### Integration Tests

| Test | Description |
|------|-------------|
| `test_save_load_round_trip` | Create mosaic → save → load → verify all state matches |
| `test_multi_sheet_session` | Save 3 sheets → list returns 3 → delete 1 → list returns 2 |
| `test_email_sends_pdf` | Save sheet → email → verify email provider SDK called with correct PDF attachment (mocked) |
| `test_new_session_starts_empty` | New session cookie → sheet list is empty |

### Top 5 High-Value Test Cases

1. **Given** a completed mosaic with edited colors in circle mode at 5mm, **When** saved and then loaded, **Then** all state is restored: mode, size, palette edits, grid data, and preview matches.

2. **Given** 3 saved sheets, **When** user clicks "Email PDF" on sheet #2, enters an email, and sends, **Then** email provider receives the correct PDF and the UI confirms success.

3. **Given** a session with 20 saved sheets, **When** user views the sheet list, **Then** a visible indicator shows "20 sheets — eligible for book order" (Phase 5 hook).

4. **Given** a saved sheet, **When** the original temp image would have been cleaned up, **Then** load still works because save copied the image to persistent storage.

5. **Given** 6 email send attempts in one hour, **When** the 6th is attempted, **Then** the request is rejected with a rate limit message.

## QA Manual Test Scenarios

| # | Scenario | Steps | Expected Result |
|---|----------|-------|-----------------|
| QA1 | Save sheet | Complete a mosaic, click Save, enter title | Sheet appears in "My Sheets" list with thumbnail |
| QA2 | Load sheet | Open "My Sheets", click a saved sheet | Full mosaic state restored; can re-edit or download |
| QA3 | Delete sheet | In sheet list, click delete on a sheet | Sheet removed from list; confirmation prompt first |
| QA4 | Email PDF | On a completed mosaic, click Email, enter address | Success message; email received with PDF attachment |
| QA5 | Multiple sheets | Create and save 3 different mosaics | All 3 appear in list with correct titles/thumbnails |
| QA6 | Refresh persistence | Save a sheet, refresh the browser | Sheet list still shows the saved sheet |
| QA7 | Sheet count badge | Save 20+ sheets | UI shows count and a "book eligible" indicator |
| QA8 | Email not configured | Start app without email env vars | Email button disabled with explanatory tooltip |
