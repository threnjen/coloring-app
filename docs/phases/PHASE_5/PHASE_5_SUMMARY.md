# Phase 5: User Persistence & Sheet Management

**Status**: Planned
**Depends on**: Phase 4 (AWS Deployment, Auth & Content Safety)
**Estimated complexity**: Large
**Cross-references**: [PHASES_OVERVIEW.md](../PHASES_OVERVIEW.md) | [PHASE_4_SUMMARY.md](../PHASE_4/PHASE_4_SUMMARY.md) | [PHASE_6_SUMMARY.md](../PHASE_6/PHASE_6_SUMMARY.md)

## Objective

Replace the in-memory storage with RDS PostgreSQL + S3 so authenticated users can save, load, and manage their coloring sheets across sessions. After this phase, a logged-in user has a persistent personal library of saved mosaic sheets tied to their Cognito identity.

## Scope

### In Scope
- RDS PostgreSQL schema: users table (linked to Cognito `sub`), sheets table (metadata, settings, palette as JSONB)
- S3 integration for generated artifacts: PDFs, preview PNGs, grid data — stored per user with pre-signed URLs for secure access
- Sheet CRUD API: save, load, list, delete sheets scoped to authenticated user
- Multi-sheet management UI: personal sheet library, thumbnails, create new / continue editing
- Data lifecycle: auto-cleanup of orphaned S3 objects, configurable storage quota per user
- Migration from in-memory `OrderedDict` to database-backed persistence
- Sheet count display and "book eligible" indicator (20+ sheets — hook for Phase 6)

### Out of Scope
- Print-on-demand / book ordering (Phase 6)
- Sharing sheets between users
- Storing original uploaded images long-term (deleted after processing, per Phase 4 policy)
- Email PDF delivery (removed from roadmap)
- User profile management (name, avatar, etc.)

## Key Deliverables

| # | Deliverable | Description | Likely Features |
|---|-------------|-------------|-----------------|
| 1 | RDS schema + data layer | PostgreSQL tables, SQLAlchemy models, database connection management | Database, models, migrations |
| 2 | S3 asset storage | Per-user S3 prefixes, pre-signed URL generation, upload/download helpers | S3, boto3 |
| 3 | Sheet CRUD API | Save, load, list, delete endpoints scoped to authenticated user | FastAPI endpoints, auth scoping |
| 4 | Sheet library UI | Frontend sheet list with thumbnails, save dialog, load/delete actions | Vanilla JS, CSS |
| 5 | Data lifecycle management | Orphan cleanup, storage quotas, session-to-user migration | Background tasks, S3 lifecycle |

## Technical Context

After Phase 4, the app runs on ECS Fargate with Cognito authentication. Key integration points:
- `src/api/routes.py` — Existing endpoints use in-memory `OrderedDict` store with LRU eviction. This phase replaces that store with RDS + S3.
- `src/models/mosaic.py` — `MosaicSheet` contains all state: grid, palette, dimensions, mode. This needs to be serializable to JSONB + S3 references.
- `src/config.py` — Will gain RDS connection string, S3 bucket name, storage quota settings.
- JWT middleware from Phase 4 provides the Cognito `sub` UUID — this becomes the user identity key for all persistence operations.

The RDS instance (db.t4g.micro PostgreSQL) is provisioned in Phase 4's VPC private subnet. This phase connects to it from the Fargate tasks.

### Database Schema (Conceptual)

- `users` — `id (PK, Cognito sub UUID)`, `created_at`, `last_login`, `sheet_count`, `storage_bytes_used`
- `sheets` — `id (UUID PK)`, `user_id (FK → users)`, `title`, `created_at`, `updated_at`, `crop_coords (JSONB)`, `editing_state (JSONB)`, `palette (JSONB)`, `mosaic_mode`, `component_size`, `grid_rows`, `grid_cols`, `s3_prefix`

### S3 Object Layout

```
s3://{bucket}/{user_id}/
  └── sheets/
      └── {sheet_id}/
          ├── preview.png       # Mosaic preview thumbnail
          ├── grid_data.json    # Serialized GridCell 2D array
          └── sheet.pdf         # Generated PDF
```

Pre-signed URLs (short TTL, e.g., 15 minutes) for all S3 reads from the frontend. No direct S3 access from the browser.

## Dependencies & Risks

- **Dependency**: Phase 4 complete — ECS Fargate running, Cognito auth working, VPC with private subnets for RDS
- **Dependency**: RDS PostgreSQL instance provisioned (can be done as part of Phase 4 infra or early in Phase 5)
- **Dependency**: S3 bucket with appropriate IAM policies for the ECS task role
- **Risk**: Migration from in-memory to database could introduce latency in the processing pipeline. **Mitigation**: Keep in-memory store for active processing; persist to DB only on explicit save. Process pipeline remains fast.
- **Risk**: S3 pre-signed URL expiration could break the UI if a user leaves a tab open too long. **Mitigation**: Frontend refreshes pre-signed URLs on tab focus; 15-minute TTL is generous enough.
- **Risk**: Storage costs could grow if users save many large PDFs. **Mitigation**: Configurable per-user quota (e.g., 100 sheets / 500MB); S3 lifecycle rules to transition old objects to Infrequent Access.
- **Risk**: First user login needs to create a user record. **Mitigation**: Upsert on first authenticated API call; Cognito post-authentication Lambda trigger is an alternative.

## Success Criteria

- [ ] Authenticated user can save a completed mosaic with a title
- [ ] User can view a list of all their saved sheets with preview thumbnails
- [ ] User can load a previously saved sheet and all state is restored: mode, size, palette edits, grid data
- [ ] User can delete a saved sheet (data removed from both RDS and S3)
- [ ] Saved sheets persist across browser sessions — close browser, reopen, log in, sheets are there
- [ ] Sheets are scoped to the authenticated user — no cross-user access
- [ ] Sheet count is displayed; 20+ sheets shows a "book eligible" indicator
- [ ] In-memory `OrderedDict` store in `routes.py` is replaced — no more LRU eviction data loss
- [ ] S3 pre-signed URLs work correctly for loading preview thumbnails in the sheet list
- [ ] Storage quota is enforced — user gets a clear message when approaching the limit

## QA Considerations

- This phase includes significant frontend/UI changes (sheet library, save dialog, thumbnails) requiring manual QA docs
- Persistence must be tested across login/logout cycles and across multiple browser sessions
- Cross-user isolation must be verified — logging in as user A should never see user B's sheets
- Pre-signed URL expiration behavior needs manual testing (leave tab open, come back)
- Mobile browser testing for sheet library layout

## Notes for Feature - Decomposer

Suggested feature boundaries:
1. **Database layer** — RDS schema, SQLAlchemy models, connection management, user upsert on first login. Foundation for everything else.
2. **S3 asset storage** — Upload/download helpers, pre-signed URL generation, per-user prefix structure, IAM policy. Can be developed in parallel with database layer.
3. **Sheet save/load API** — CRUD endpoints that combine DB metadata writes with S3 asset uploads/downloads. Depends on both DB and S3 layers.
4. **Sheet library UI** — Frontend sheet list, save dialog, load/delete buttons, thumbnails via pre-signed URLs, sheet count badge. Depends on the API layer.
5. **Data lifecycle + quotas** — Storage tracking, quota enforcement, orphan cleanup, S3 lifecycle configuration. Can be developed after core CRUD works.

Key separation of concerns: The database stores metadata and lightweight JSON state. S3 stores binary artifacts (PNGs, PDFs, grid data). The API layer coordinates both. The existing `MosaicSheet` model should gain serialization methods but should not become database-aware — keep the data layer separate from the domain model.
