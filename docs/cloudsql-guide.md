# Cloud SQL Connectivity and Connection Pool Sizing

## Connection Strategy

### 1. Production Cloud Run Integration (Unix Domain Sockets)
Google Cloud Run provides native, secure integration with Cloud SQL instances without requiring public IP endpoints or credentials over the public internet:

- **Annotation**: `run.googleapis.com/cloudsql-instances: PROJECT:REGION:INSTANCE`
- **Socket Path**: `/cloudsql/PROJECT:REGION:INSTANCE/.s.PGSQL.5432`
- **Connection URL Format**:
  ```text
  postgresql+asyncpg://app_user:PASSWORD@/database_name?host=/cloudsql/PROJECT:REGION:INSTANCE
  ```

### 2. Local Development & Testing (Cloud SQL Auth Proxy)
When developing locally against a remote development Cloud SQL instance, use the Cloud SQL Auth Proxy:
```bash
./infrastructure/scripts/cloud-sql-proxy.sh
```
Or via Docker:
```bash
docker run --rm -p 127.0.0.1:5432:5432 \
  gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest \
  --address 0.0.0.0 --port 5432 \
  PROJECT_ID:REGION:INSTANCE_NAME
```
Local `DATABASE_URL` then points to:
```text
postgresql+asyncpg://app_user:PASSWORD@127.0.0.1:5432/interview_ready
```

---

## Connection Pool Sizing & Sizing Formula

> [!WARNING]
> In serverless architectures like Google Cloud Run, horizontal container autoscaling dynamically multiplies the total database connections.

### Sizing Formula

$$\text{Max DB Connections} = \text{Cloud Run Max Instances} \times (\text{DB\_POOL\_SIZE} + \text{DB\_MAX\_OVERFLOW})$$

### Recommended Configuration

| Parameter | Recommended Value | Rationale |
| --- | --- | --- |
| `maxScale` (Cloud Run) | `20` | Caps maximum concurrent container replicas |
| `DB_POOL_SIZE` | `5` | Keeps base pool light per container |
| `DB_MAX_OVERFLOW` | `10` | Permits short surges for concurrent queries |
| **Max Potential Connections** | **300** | Fits comfortably within PostgreSQL `max_connections` (500) |
| `DB_POOL_RECYCLE` | `1800` (30 mins) | Prevents stale connections caused by Cloud SQL TCP timeouts |
| `DB_POOL_PRE_PING` | `true` | Validates connection liveness before execution |
| `DB_POOL_TIMEOUT` | `30` | Fails fast with clear errors if pool is saturated |

---

## PostgreSQL Database Flags

Ensure the Cloud SQL PostgreSQL instance is configured with appropriate server-side parameters:
- `max_connections`: `>= 500` (adjust according to allocated RAM)
- `statement_timeout`: `30000` (30 seconds to prevent rogue locking queries)
- `idle_in_transaction_session_timeout`: `60000` (60 seconds)
