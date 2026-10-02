# Module 01 — Repository Foundation

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Create the project skeleton and local development foundation without implementing business features.

## Tasks

### Monorepo
Create:
- `apps/api`
- `apps/web`
- `apps/desktop`
- `packages/api-types`
- `packages/ui`
- `packages/config`
- `infrastructure`
- `docs`
- `.github/workflows`

### FastAPI foundation
Configure:
- Python 3.11+
- FastAPI
- SQLAlchemy 2 async
- asyncpg
- Alembic
- Pydantic v2 settings
- firebase-admin
- Redis client
- httpx
- pytest / pytest-asyncio
- ruff
- mypy

Create:
- application factory/startup
- `/health/live`
- `/health/ready`
- configuration loading
- async database session factory
- Redis connection factory
- structured logging
- request ID middleware
- centralized API exception/error envelope

### Next.js foundation
Create Next.js 15 App Router app with:
- TypeScript strict mode
- Tailwind
- Lucide React
- base route structure
- basic health/home page
- environment-variable validation

### Tauri foundation
Create Tauri v2 + React + TypeScript shell with:
- minimal secure permissions
- no unnecessary shell/fs permissions
- placeholder main application page

### Developer experience
Add:
- root README
- `.editorconfig`
- `.gitignore`
- example environment files with no secrets
- local development instructions
- lint/type/test commands
- Docker Compose only for local PostgreSQL + Redis if useful

## Acceptance criteria

- API starts locally.
- Web starts locally.
- Desktop shell starts locally.
- API can connect to local Postgres and Redis.
- `/health/live` and `/health/ready` work.
- No business-domain database tables yet.
- No secrets committed.
