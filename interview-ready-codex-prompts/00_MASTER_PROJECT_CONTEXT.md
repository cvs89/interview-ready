# Interview Ready — Master Project Context for Codex

You are acting as a Staff/Principal Full-Stack Engineer and Systems Architect.

Build a production-ready, modular, high-concurrency Mock Interview Marketplace named **Interview Ready**.

## Product model

This is **not a credit-wallet or escrow platform**.

The commercial flow is:

1. An approved interviewer creates paid interview availability slots.
2. A candidate discovers an interviewer and selects a specific slot.
3. The platform temporarily reserves the slot.
4. The candidate pays the real-money price for that slot.
5. A trusted payment-provider webhook confirms payment.
6. The booking becomes confirmed and the slot becomes booked.
7. Candidate and interviewer join through the desktop application around the scheduled time.
8. The interviewer completes the interview and submits structured feedback/rubric.
9. The candidate can view feedback and optionally submit a rating/review.

For MVP, assume the platform merchant receives candidate payments. Interviewer payouts can be handled separately unless explicitly implemented in a later module.

## Mandatory technical stack

### Backend
- Python 3.11+
- FastAPI, async
- SQLAlchemy 2.0 async
- asyncpg
- Alembic
- Pydantic v2
- firebase-admin SDK
- PostgreSQL
- Redis for one-time desktop tickets and rate-limiting primitives
- LiveKit server SDK for room tokens
- pytest + pytest-asyncio + httpx
- Ruff + mypy

### Web
- Next.js 15
- App Router
- TypeScript strict mode
- Tailwind CSS
- Lucide React
- Firebase Web SDK
- Fetch or Axios with automatic Firebase ID token injection
- Vitest + React Testing Library
- Playwright for critical flows

### Desktop
- Tauri v2
- Rust
- React + TypeScript
- Custom URL scheme: `interviewapp://`
- LiveKit WebRTC client
- Strict least-privilege Tauri permissions

### Infrastructure
- PostgreSQL on Google Cloud SQL
- FastAPI on Google Cloud Run
- Next.js on Cloud Run behind Firebase Hosting rewrites
- Redis-compatible managed service
- Google Secret Manager
- Google Cloud Storage for private files where needed
- Cloud Tasks and/or Pub/Sub for durable async jobs
- Google Cloud Logging/Monitoring
- Optional Sentry/OpenTelemetry

## Core security principles

- Never trust role, user ID, price, booking ownership, or payment state from the client.
- Firebase ID tokens must be verified server-side.
- Authorization must enforce both RBAC and resource ownership.
- Payment success must be driven by verified provider webhook events.
- Never log Firebase tokens, desktop tickets, LiveKit tokens, payment secrets, or complete deep-link URLs.
- Desktop login tickets must be cryptographically random, server-stored as hashes, one-time, and short-lived.
- Backend must enforce interview join windows even if the frontend disables the button.
- Financial amounts are integer minor units, never floats.
- Database constraints must protect invariants where possible.
- Use UTC timestamps in storage and convert to local timezone in UI.
- Do not introduce a credit balance, wallet, or escrow model unless explicitly asked later.

## Core repository structure

Use this monorepo unless the repository already has an established compatible structure:

```text
interview-ready/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── db/
│   │   │   ├── models/
│   │   │   ├── schemas/
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── integrations/
│   │   │   ├── workers/
│   │   │   └── main.py
│   │   ├── alembic/
│   │   └── tests/
│   ├── web/
│   └── desktop/
├── packages/
│   ├── api-types/
│   ├── ui/
│   └── config/
├── infrastructure/
├── .github/workflows/
└── docs/
```

## Coding rules

1. Keep routers/controllers thin.
2. Put business rules in services.
3. Put persistence logic in repositories.
4. Use explicit Pydantic request/response schemas.
5. Use SQLAlchemy 2.0 typed mappings.
6. Avoid hidden side effects.
7. Add tests with each module.
8. Add DB constraints and indexes, not only application checks.
9. Use a consistent API error envelope:
   ```json
   {
     "error": {
       "code": "SLOT_ALREADY_RESERVED",
       "message": "The selected slot is no longer available.",
       "request_id": "..."
     }
   }
   ```
10. Use structured logs with request/correlation IDs.
11. Do not implement speculative features outside the requested module.
12. Do not rewrite unrelated files.

## Required delivery behavior for every Codex task

For each module prompt:

1. Inspect the current repository first.
2. Summarize the existing relevant structure.
3. State the implementation plan.
4. Implement only the requested module.
5. Add/update migrations if required.
6. Add tests.
7. Run relevant lint/type/test commands where possible.
8. Report:
   - files added
   - files changed
   - migrations created
   - tests added
   - commands run
   - known limitations
9. Do not move to the next module automatically.

Use the remaining module prompt files in numeric order.
