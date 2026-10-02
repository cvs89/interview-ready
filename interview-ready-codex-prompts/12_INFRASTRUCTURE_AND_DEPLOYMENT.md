# Module 12 — Production Docker, Cloud Run, Firebase Hosting, Cloud SQL, Secrets

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Prepare production deployment architecture without weakening security.

## FastAPI Dockerfile

Create multi-stage image:
- pinned Python base
- dependency installation separated for cache efficiency
- non-root runtime user
- no compilers/build tooling in final image where avoidable
- health support
- sensible Uvicorn command for Cloud Run
- environment-driven port

Do not bake secrets into image.

## Next.js Dockerfile

Production standalone build suitable for Cloud Run.

## Firebase Hosting

Configure rewrites conceptually as:

- `/api/**` -> API Cloud Run service
- `/**` -> Next.js Cloud Run service

Ensure Next.js static assets continue to resolve correctly.

## Cloud SQL

Production:
- use Cloud Run + Cloud SQL supported connector/integration
- do not require a sidecar Auth Proxy inside production service unless intentionally documented

Local development:
- document Cloud SQL Auth Proxy option

## SQLAlchemy pool limits

Make pool settings configurable, for example:
- `pool_size`
- `max_overflow`
- `pool_timeout`
- `pool_recycle`
- `pool_pre_ping`

Document that Cloud Run horizontal scaling multiplies DB connections.

## Redis

Configure managed Redis connection through secrets/environment.

## Secret Manager

Use Google Secret Manager for:
- DB credentials if applicable
- Firebase service-account configuration
- LiveKit API secret
- session JWT signing keys
- payment-provider secrets
- Redis credentials
- webhook signing secrets

## Cloud Storage

Prepare storage config for profile/verification files if file uploads are enabled.
Private assets must use signed/authenticated access.

## Migrations

Create a safe deployment migration strategy.
Do not run Alembic simultaneously from every API replica.

Prefer:
- CI/CD migration job
- dedicated Cloud Run job
- or equivalent single-run deployment step

## Deliverables

- Dockerfiles
- firebase.json
- deployment docs
- environment variable reference
- Cloud SQL connectivity guide
- migration deployment guide
