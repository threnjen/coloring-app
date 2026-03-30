# Phase 4: AWS Deployment, Authentication & Content Safety

**Status**: Planned
**Depends on**: Phase 1 (Core Pipeline POC)
**Estimated complexity**: Large
**Cross-references**: [PHASES_OVERVIEW.md](../PHASES_OVERVIEW.md) | [PHASE_5_SUMMARY.md](../PHASE_5/PHASE_5_SUMMARY.md)

---

## Objective

Deploy the existing app to AWS with containerized compute, social login authentication, and automated content moderation. After this phase, the app is publicly accessible on the internet, users sign in via Google/Facebook/Apple, and uploaded images are scanned for prohibited content before processing. The app still uses in-memory state (no persistence yet) — this phase is purely about the platform shift.

## Scope

### In Scope
- Dockerize the FastAPI application (multi-stage build, health check endpoint)
- ECS Fargate service with ALB, auto-scaling policy, and CloudWatch monitoring
- Cognito User Pool with social identity providers (Google, Facebook, Apple)
- Cognito Hosted UI for login/signup/redirect flow
- JWT validation middleware in FastAPI for all authenticated endpoints
- Amazon Rekognition content moderation on image upload
- CloudFront distribution for static assets (HTML/JS/CSS)
- VPC setup: public subnets (ALB, NAT Gateway), private subnets (Fargate tasks)
- Health check endpoint (`/health`) and basic operational monitoring

### Out of Scope
- User data persistence (Phase 5 — RDS + S3)
- Sheet save/load/management (Phase 5)
- Print-on-demand (Phase 6)
- Email PDF delivery (removed from roadmap)
- Username/password authentication (social login only)
- Custom login UI (using Cognito Hosted UI)
- Domain name and Route 53 (will be added when domain is acquired)

## Key Deliverables

| # | Deliverable | Description | Likely Features |
|---|-------------|-------------|-----------------|
| 1 | Dockerized application | Multi-stage Dockerfile, health check, container-compatible config | Docker, FastAPI config |
| 2 | ECS Fargate deployment | Task definition, service, ALB, auto-scaling, CloudWatch alarms | ECS, ALB, CloudWatch |
| 3 | Cognito authentication | User Pool, social IdPs, Hosted UI, JWT middleware | Cognito, FastAPI auth |
| 4 | Content moderation | Rekognition scan on upload, reject flagged content, delete originals post-processing | Rekognition, upload pipeline |
| 5 | CloudFront + static serving | CloudFront distribution, S3 origin for static assets, cache configuration | CloudFront, S3 |

## Technical Context

The app is currently a single-server FastAPI application serving both API and static files. Key files:
- `src/main.py` — FastAPI app instantiation and startup
- `src/config.py` — Module-level constants, env var overrides, `validate_config()`
- `src/api/routes.py` — All HTTP endpoints, in-memory `OrderedDict` store
- `static/` — Vanilla HTML/JS/CSS frontend, no build step

The image processing stack (rembg, OpenCV, scikit-learn, Pillow) requires ~4GB memory at peak. The rembg ONNX model is ~100MB. These constraints drive the Fargate task sizing (1 vCPU, 4GB).

The frontend is vanilla JS with no auth concept. Login/logout UI and token management will be new. The Cognito Hosted UI handles the OAuth redirect flow, so the frontend needs to handle the callback and attach JWTs to API requests.

## Dependencies & Risks

- **Dependency**: Phase 1 must be complete (working pipeline to deploy)
- **Dependency**: AWS account with appropriate IAM permissions
- **Dependency**: Social IdP developer accounts (Google Cloud Console, Facebook Developer, Apple Developer) for OAuth client credentials
- **Risk**: Social IdP credential setup requires domain verification for some providers — may need temporary workaround for pre-domain deployment. **Mitigation**: Use ALB hostname initially; switch to custom domain later.
- **Risk**: Rekognition false positives could reject legitimate images. **Mitigation**: Use moderate confidence threshold (e.g., 75%); log rejections for review; allow threshold tuning via config.
- **Risk**: ECS Fargate cold task startup takes 30-60s for pulling the Docker image. **Mitigation**: Keep minimum task count at 1; use ECR image caching.
- **Risk**: rembg model file (~100MB) increases Docker image size and pull time. **Mitigation**: Multi-stage build, include model in image rather than downloading at runtime.

## Success Criteria

- [ ] App accessible via ALB public URL (and eventually CloudFront)
- [ ] User can sign in via Google, Facebook, or Apple through Cognito Hosted UI
- [ ] Unauthenticated requests to API endpoints return 401
- [ ] `/health` endpoint returns 200 (used by ALB health checks)
- [ ] Upload of a benign image succeeds and proceeds through the pipeline normally
- [ ] Upload of a flagged image (nudity/violence) is rejected with a clear error message before processing
- [ ] Original uploaded images are deleted from local storage after mosaic generation completes
- [ ] Static assets served via CloudFront with proper cache headers
- [ ] ECS service auto-scales from 1 to N tasks based on CPU utilization
- [ ] CloudWatch alarms fire on sustained high CPU or task failures

## QA Considerations

- This phase includes frontend/UI changes (login flow, moderation rejection messages) requiring manual QA docs
- Auth flows must be tested across all three social providers (Google, Facebook, Apple)
- Content moderation must be tested with known-clean and known-flagged images
- Mobile browser testing for Cognito Hosted UI redirect flow

## Notes for Feature - Decomposer

Suggested feature boundaries:
1. **Dockerization** — Dockerfile, health endpoint, container-compatible config changes. Can be developed and tested locally before any AWS setup.
2. **ECS Fargate + ALB** — Infrastructure deployment, task definition, service configuration, auto-scaling. Depends on Docker image.
3. **Cognito + Auth middleware** — User Pool creation, social IdP setup, Hosted UI config, FastAPI JWT middleware, frontend login/logout flow. Can be partially developed in parallel with ECS.
4. **Content moderation** — Rekognition integration in the upload endpoint, rejection flow, original image cleanup. Depends on the app being deployed (needs AWS credentials).
5. **CloudFront + static assets** — Split static serving from API, configure CloudFront distribution. Can be done last as a polish step.

Integration points: Auth middleware affects all API routes. Content moderation modifies the upload endpoint. CloudFront changes how the frontend is served. These three features touch different parts of the codebase but must be tested together end-to-end.
