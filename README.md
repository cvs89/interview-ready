# Interview Ready

Production-oriented monorepo for the Interview Ready mock-interview marketplace.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for completed modules, pending work, validation results, blockers, and AI handoff instructions.

This repository currently contains the Module 01 foundation only. It intentionally has no business-domain models or features.

## Prerequisites

- Python 3.11+
- Node.js 20+
- Rust stable and the [Tauri v2 prerequisites](https://v2.tauri.app/start/prerequisites/)
- Docker with Compose

## Local services

```bash
docker compose up -d postgres redis
```

The sample credentials are only for local development. Copy each `.env.example` to `.env` in the same directory before starting an app.

## API

```bash
cd apps/api
uv sync --extra dev
cp .env.example .env
uv run uvicorn app.main:create_app --factory --reload
```

The liveness endpoint is `http://localhost:8000/health/live`. Readiness checks PostgreSQL and Redis at `/health/ready` and returns HTTP 503 until both dependencies respond.

Apply database migrations before serving authenticated traffic:

```bash
uv run alembic upgrade head
```

For local Firebase authentication, set `GOOGLE_APPLICATION_CREDENTIALS` to an uncommitted service-account JSON file. Cloud Run should use Application Default Credentials through its service account.

```bash
uv run pytest
uv run ruff check .
uv run mypy app
```

## Web

```bash
npm install
cp apps/web/.env.example apps/web/.env.local
npm run dev:web
```

```bash
npm run lint:web
npm run typecheck:web
npm run test:web
```

## Desktop

Install packages first, then:

```bash
cp apps/desktop/.env.example apps/desktop/.env
npm run dev:desktop
```

Use `npm run check:desktop` for TypeScript and Rust checks.
