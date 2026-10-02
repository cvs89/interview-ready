# Production Database Migration Strategy

## Core Principle: Single Execution Guarantee

> [!IMPORTANT]
> **Never execute Alembic migrations during API container startup.**
> Running `alembic upgrade head` inside container initialization causes race conditions, lock contention, and duplicate DDL execution when multiple Cloud Run replicas scale up concurrently.

---

## Migration Architecture

Migrations must be executed as a dedicated, synchronous deployment step prior to routing production traffic to newly deployed API versions.

```
       [ CI/CD Pipeline / Release Dispatch ]
                         │
                         ▼
   ┌───────────────────────────────────────────┐
   │         Step 1: Execute Migration         │
   │    (Cloud Run Job / CI Single Runner)     │
   │       `alembic upgrade head`              │
   └─────────────────────┬─────────────────────┘
                         │
            ┌────────────┴────────────┐
            │ Success                 │ Failure
            ▼                         ▼
   ┌───────────────────┐    ┌───────────────────┐
   │ Step 2: Deploy    │    │ Abort Deployment  │
   │ API Cloud Run     │    │ & Alert On-Call   │
   │ Service Replicas  │    └───────────────────┘
   └───────────────────┘
```

---

## Deployment Steps

### 1. One-Shot Cloud Run Job
Use the dedicated `interview-ready-migrations` Cloud Run Job:
```bash
# Update job with the latest container image
gcloud run jobs deploy interview-ready-migrations \
  --image="${API_IMAGE}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --set-cloudsql-instances="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUD_SQL_INSTANCE}" \
  --command="alembic" \
  --args="upgrade,head" \
  --set-secrets="DATABASE_URL=interview-ready-database-url:latest"

# Execute migration synchronously and check exit code
gcloud run jobs execute interview-ready-migrations \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --wait
```

### 2. Verification Commands
```bash
# Check currently applied revision
uv run alembic current

# Review migration history
uv run alembic history --verbose

# Inspect SQL before applying
uv run alembic upgrade head --sql
```

---

## Zero-Downtime Migration Pattern (Expand / Contract)

When performing breaking schema changes (e.g. column renames, type conversions, table splits), follow the **Expand / Contract** pattern across releases:

1. **Expand (Release N)**:
   - Add new column or table with nullable or default values.
   - Deploy backend code that writes to both old and new columns, and reads from old column.
2. **Backfill**:
   - Run a backfill job to populate new columns from existing data.
3. **Switch (Release N+1)**:
   - Deploy backend code that reads from the new column and writes to both.
4. **Contract (Release N+2)**:
   - Drop the deprecated old column in a final migration.

---

## Rollback Procedures

If a migration fails during execution:
1. Inspect the migration job logs in Google Cloud Logging:
   ```bash
   gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="interview-ready-migrations"' --limit=50
   ```
2. For reversible migrations, downgrade to the previous revision target:
   ```bash
   alembic downgrade 20261002_0006
   ```
