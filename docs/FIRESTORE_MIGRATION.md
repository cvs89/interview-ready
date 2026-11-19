# FastAPI + Firestore migration

Implementation date: 19 November 2026. This is an **opt-in backend**, not a production cutover. No Cloud SQL resource has been deleted, upgraded or modified. No cloud database or billing plan has been created. Existing uncommitted SQL concurrency and frontend changes were preserved.

## Hosted database selected by the owner

The owner subsequently created `projects/interview-ready-52479/databases/default`,
Standard edition / Firestore Native, in `eur3` (Europe). The API reports
`freeTier: true`. Its ID is **`default` without parentheses**, not `(default)`.
The local ignored `apps/api/.env` now explicitly selects that database.

`firebase.firestore.hosted.json` targets only this named database. Keep
`firebase.firestore.json` for local emulator tests; do not deploy that emulator
configuration to the hosted project, since it targets the different `(default)` ID.
Rules/index deployment is approved for this database; production API cutover is not.
See the latest hosted-setup entry in `PROJECT_STATUS.md` for verification results.

Local Python requires Application Default Credentials (`gcloud auth application-default login`),
which are separate from `gcloud auth login`. Redis must also be running for the
full API readiness check and desktop tickets. Do not enable the emulator host
environment variable when accessing the hosted database.

## Enablement

`DATABASE_BACKEND=firestore` selects Firestore for every existing API route at both root and `/api/v1`. The compatibility default remains `postgresql` so an existing deployment is not silently switched to an empty database. `FIRESTORE_PROJECT_ID` is required (or `GCP_PROJECT_ID`); `FIRESTORE_DATABASE_ID` defaults to `(default)`.

FastAPI remains the database gateway. Firebase Authentication, response schemas, Redis-backed one-use desktop tickets, and LiveKit token generation remain. PostgreSQL/Alembic code is retained for old deployments and migration/reference purposes; **Firestore mode does not create a SQL engine and does not run Alembic**.

## Local setup: no hosted database required

Prerequisites: Python/uv, Node, Java 21+, and Redis. A local Firestore emulator is not a production database and normally loses its data when stopped unless explicitly exported/imported.

From the repository root:

```sh
npx --yes firebase-tools@15.37.0 emulators:start --only firestore \
  --project demo-interview-ready --config firebase.firestore.json
```

In another terminal, start Redis with the existing Compose service (Docker must be running), then start the API:

```sh
docker compose up -d redis
cd apps/api
uv sync --frozen --extra dev
export DATABASE_BACKEND=firestore
export FIRESTORE_PROJECT_ID=demo-interview-ready
export FIRESTORE_EMULATOR_HOST=127.0.0.1:8080
export APP_ENV=development
uv run uvicorn app.main:create_app --factory --reload
```

Keep your existing Firebase Authentication configuration. Firestore emulation does not emulate login by itself. Do not overwrite an existing `.env` containing your settings. `.env.firestore.example` lists the database settings. **Export `FIRESTORE_EMULATOR_HOST` in the process environment**, not only the dotenv file, because Google's SDK consumes it directly. Demo projects without an emulator fail startup; staging/production with an emulator also fails startup.

`/health/ready` checks both Firestore and Redis. Opening `/health/live` alone does not prove database connectivity. Local-only tests use mocked authentication; they do not bypass authentication in the running app.

## Storage and safety design

| Area | Implementation |
| --- | --- |
| Identity | Transactional Firebase UID/email bindings, preserved UUID API identities, active-account checks; verified-email allowlist for admin bootstrap, never client role claims. |
| Profiles/skills | Profiles, verification records, deterministic uniqueness keys, skill summaries, anonymous public presentation. |
| Availability | Slot documents plus a per-interviewer schedule guard. Every creation/reschedule touches the guard to prevent concurrent empty-query overlap races. |
| Reservation | Slot ownership and booking document committed together. Expiry checked with backend time, never dependent on TTL deletion. Historical bookings remain when a slot is rebooked. |
| Payments | Stable checkout idempotency keys, signed webhooks, provider/amount/currency binding, deduplicated event IDs, terminal-state protection, late-payment refund jobs. |
| Refunds | Durable jobs and provider idempotency keys. `process_refunds` task executes external refunds outside transactions; never marks a payment refunded before provider success. |
| Sessions | One-use Redis tickets; current booking/user/role revalidation on exchange; one session per booking; opaque room names. |
| Feedback | Private notes in separate documents; candidate responses cannot read those documents. Submission completes booking and ends session atomically. |
| Reviews | One document per booking and transactional rating summary. |
| Notifications | In-app notifications committed with business state; external delivery intent stored in `notification_outbox`. Email/FCM transport is not newly provisioned by this migration. |
| Audit | Append-only application events with recursive sensitive-key redaction. IAM administrators can still modify documents; this is not a tamper-proof compliance ledger. |
| Tasks | Firestore HTTP task execution requires a Firebase-authenticated admin. Do not send anonymous requests to `/internal/tasks/process`. |

External provider calls never execute within retried Firestore callbacks. Transaction writes are buffered so all reads precede writes. SDK conflict retries are supplemented with bounded jittered retries for read-time lock conflicts; exhausted contention returns `TRANSACTION_BUSY` (409) with `Retry-After`.

## Query and cost limits

Legacy APIs use offset-based filtering and totals. Some complex directory/admin queries use a **bounded scan**, capped by `FIRESTORE_SCAN_LIMIT` (default 1000). If exceeded, they return `QUERY_TOO_BROAD`, never silently incomplete results. At larger scale these endpoints need cursor pagination and query-specific read models. Offsets, repeated auth metadata writes, and directory enrichment incur reads/writes; this is not a guarantee of zero bills.

Composite indexes are in `firestore.indexes.json`. The emulator does not prove that production indexes are built. Validate all directory filters and ordering in a hosted test database before cutover. Rules deny all direct browser/mobile database access; server access uses IAM plus API ownership/role checks.

Free Firestore quotas are not free managed backup/PITR. Backend hosting, Redis, LiveKit, payments and external notifications are separate services. See [Firestore pricing](https://firebase.google.com/docs/firestore/pricing).

## Hosted setup / production cutover: not performed

1. Determine whether suspended `interview-ready-db` contains real records. Do not delete it. A Firestore database cannot retrieve data from a suspended SQL instance automatically.
2. Choose Firestore Standard/Native database location, confirm applicable free quota and billing state. Do not enable billing simply to run a test. Creating a real database and selecting its location needs owner approval.
3. Grant the API service account only appropriate Firestore data access (commonly `roles/datastore.user`), not Owner. Keep existing Firebase Auth/Redis/LiveKit permissions. Hosted local testing uses application-default credentials, not just `gcloud auth login`.
4. Review and deploy only the Firestore rules/indexes, not hosting:
   `firebase deploy --only firestore --config firebase.firestore.hosted.json --project interview-ready-52479`
5. For **test-only data**, recreate accounts/profiles/skills via existing APIs. For important SQL data, obtain a recoverable export first and implement a reviewed transformation preserving UUIDs, identity/email/profile keys, private-note separation, payment event bindings, and rating summaries. An automatic SQL-data importer is deliberately not provided without a source-data audit.
6. Configure the existing API secrets and a real payment provider (`PAYMENT_PROVIDER=stripe`) before paid traffic. Mock payments are rejected in Firestore production mode.
7. Build a tested API image. The explicit script `infrastructure/scripts/deploy-firestore-api.sh` removes SQL attachment/configuration and selects Firestore. It does not grant IAM or create the database. Do not use the old SQL `deploy.sh` for Firestore; it requires SQL and runs Alembic.
8. Schedule authenticated expiry/reminder/refund tasks and monitor pending refund/notification jobs. A script invocation alone does not create a scheduler. Real email/FCM delivery remains a separate integration; pending outbox documents must not be mistaken for delivered messages.
9. Run the complete booking → signed payment → desktop ticket → assessment → review journey. Verify backup/recovery and rollback before accepting real payments.

Rollback is not just changing `DATABASE_BACKEND` after Firestore has accepted new writes: those writes are not mirrored to SQL. Pause writes and reconcile/export new records before any rollback.

## Verification

```sh
# Unit/business contracts; emulator cases skip unless the emulator host is set.
cd apps/api
uv run pytest tests/test_firestore_backend.py -v
uv run mypy app

# From repository root: run both memory and real emulator cases.
npx --yes firebase-tools@15.37.0 emulators:exec --only firestore \
  --project demo-interview-ready --config firebase.firestore.json \
  'cd apps/api && uv run pytest tests/test_firestore_backend.py -v'
```

`.github/workflows/firestore.yml` runs the real emulator suite in CI. Memory tests alone do not prove Firestore locking or index behavior. Existing SQL tests remain in place; consult `PROJECT_STATUS.md` for actual results and outstanding pre-existing failures.

For an explicitly approved hosted smoke test, run from `apps/api`:

```sh
uv run python scripts/firestore_hosted_smoke.py \
  --project interview-ready-52479 --database default --confirm-test-writes
```

It creates only synthetic records under a random `_smoke_tests/{id}` namespace,
uses mock payments, and removes its own records in `finally`. This consumes a small
number of database reads/writes/deletes. It does not test real Firebase sign-in,
real Stripe payments, Redis, LiveKit or browser/desktop UI. The optional
`--gcloud-credentials` flag uses a short-lived CLI access token in memory when ADC
is not configured; it is a diagnostic convenience, not persistent application auth.
