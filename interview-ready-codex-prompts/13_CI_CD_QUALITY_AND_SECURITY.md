# Module 13 — CI/CD, Quality Gates, Security Baseline

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Build a repeatable pipeline for backend, web, desktop, migrations, and security checks.

## GitHub Actions or repository-standard CI

PR pipeline:

### API
- install dependencies
- ruff
- mypy
- pytest
- PostgreSQL integration tests

### Web
- install dependencies
- ESLint
- TypeScript type check
- unit tests
- production build

### Desktop
- TypeScript checks
- Rust `cargo fmt --check`
- `cargo clippy`
- unit tests
- platform-appropriate build validation where feasible

### General
- dependency vulnerability scan
- secret scanning
- no `.env` secrets
- migration validation

## Main/deploy pipeline

Implement or document:
- build API image
- build web image
- push to Artifact Registry
- run one-time DB migration job
- deploy API Cloud Run
- deploy web Cloud Run
- deploy Firebase Hosting config
- smoke tests

Do not automatically publish desktop installers unless signing/notarization requirements are configured.

## Security headers

Apply appropriate:
- CSP
- HSTS at production edge
- Referrer-Policy
- X-Content-Type-Options
- frame restrictions

## Rate limiting

Implement backend primitives for:
- desktop ticket mint
- desktop ticket exchange
- booking reservation
- payment/checkout endpoints
- expensive search

Use user + IP-aware strategy where appropriate.

## Acceptance criteria

No deployment proceeds when critical unit/integration tests fail.
