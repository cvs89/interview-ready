# Module 15 — Final Production Readiness Review

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Do not add major features. Review the completed repository for production readiness and fix only verified defects/gaps.

## Review areas

### Domain integrity
- booking state machine
- slot state machine
- payment state transitions
- rubric/review permissions

### Concurrency
- row locking
- unique constraints
- exclusion constraints
- idempotency
- reservation-expiry races

### Security
- Firebase verification
- RBAC
- ownership checks
- admin boundaries
- desktop ticket one-time behavior
- LiveKit token scoping
- secrets
- logging hygiene
- Tauri permissions
- CSP/security headers

### Database
- indexes
- FK constraints
- enum consistency
- UTC timestamps
- DB pool settings
- migration safety

### Reliability
- durable jobs
- retries
- webhook deduplication
- graceful failure behavior

### Observability
- request IDs
- structured logs
- error reporting
- health checks
- useful metrics

### Quality
- backend tests
- frontend tests
- E2E
- concurrency tests
- CI gates

### Deployment
- Docker
- Cloud Run
- Cloud SQL
- Redis
- Secret Manager
- Firebase Hosting
- migration execution

## Output

Produce:
1. `docs/production-readiness-report.md`
2. categorized issues:
   - BLOCKER
   - HIGH
   - MEDIUM
   - LOW
3. exact file references for every finding
4. remediation status
5. remaining manual infrastructure/product decisions

Do not declare the platform production-ready if any BLOCKER remains.
