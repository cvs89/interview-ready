# Production Deployment and Architecture Guide

## Overview

Interview Ready utilizes a cloud-native, serverless architecture on Google Cloud Platform (GCP) and Firebase:

```
                  +-------------------------------------------------+
                  |                Firebase Hosting                 |
                  |             (Global CDN & SSL Edge)             |
                  +------------------------+------------------------+
                                           |
                   +-----------------------+-----------------------+
                   |                                               |
                   v (/api/**)                                     v (/**)
    +------------------------------+                +------------------------------+
    |     FastAPI Backend          |                |      Next.js 15 Web App      |
    |  Cloud Run Service (API)     |                |  Cloud Run Service (Web)     |
    |   (Auto-scaling: 1-20)       |                |   (Auto-scaling: 1-20)       |
    +--------------+---------------+                +------------------------------+
                   |
       +-----------+-----------+
       |                       |
       v                       v
+---------------+      +---------------+
|   Cloud SQL   |      |  Memorystore  |
|  (PostgreSQL) |      |    (Redis)    |
+---------------+      +---------------+
```

---

## Component Topology

| Service | Technology | Hosting Platform | Sizing / Scale |
| --- | --- | --- | --- |
| **API Backend** | Python 3.12 / FastAPI | Google Cloud Run (gen2) | 1-20 instances, 1 vCPU, 1 GiB RAM, 80 concurrency |
| **Web Frontend** | Node.js 22 / Next.js 15 | Google Cloud Run (gen2) | 1-20 instances, 1 vCPU, 1 GiB RAM, 100 concurrency |
| **Edge Routing** | Firebase Hosting | Google CDN & Edge | Global Anycast, SSL, Asset Caching |
| **Database** | PostgreSQL 16 | Google Cloud SQL | db-custom-2-7680 (HA enabled), Automated backups |
| **Cache & Queue** | Redis 7 | Google Cloud Memorystore | Basic / Standard HA tier, VPC direct peering |
| **Video Infrastructure** | LiveKit WebRTC | LiveKit Cloud / Self-hosted | Dedicated WebRTC media servers |
| **Secrets** | GCP Secret Manager | Cloud KMS backed | Automatic versioning & IAM role access |
| **Object Storage** | Google Cloud Storage | GCS Multi-region | Signed URL authenticated access |

---

## Deployment Steps

### 1. Prerequisites
- Google Cloud Project created with billing enabled.
- GCP APIs enabled:
  ```bash
  gcloud services enable \
    run.googleapis.com \
    sqladmin.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    redis.googleapis.com \
    storage.googleapis.com \
    firebase.googleapis.com
  ```
- Artifact Registry Docker repository created:
  ```bash
  gcloud artifacts repositories create interview-ready \
    --repository-format=docker \
    --location=us-central1
  ```

### 2. Secret Manager Provisioning
Create required production secrets in Secret Manager:
```bash
echo -n "postgresql+asyncpg://app_user:DB_PASSWORD@/interview_ready?host=/cloudsql/PROJECT:REGION:INSTANCE" | \
  gcloud secrets create interview-ready-database-url --data-file=-

echo -n "redis://:REDIS_PASSWORD@10.0.0.3:6379/0" | \
  gcloud secrets create interview-ready-redis-url --data-file=-

echo -n "GENERATED_64_CHAR_HEX_SESSION_SECRET" | \
  gcloud secrets create interview-ready-session-jwt-secret --data-file=-

echo -n "WEBHOOK_HMAC_SIGNING_SECRET" | \
  gcloud secrets create interview-ready-webhook-signing-secret --data-file=-

echo -n "LIVEKIT_API_KEY" | \
  gcloud secrets create interview-ready-livekit-api-key --data-file=-

echo -n "LIVEKIT_API_SECRET" | \
  gcloud secrets create interview-ready-livekit-api-secret --data-file=-

echo -n "wss://livekit.yourdomain.com" | \
  gcloud secrets create interview-ready-livekit-url --data-file=-
```

### 3. Service Deployment Architecture (Cloud Run)

#### Backend (`interview-ready-api`):
- **Dockerfile**: `apps/api/Dockerfile`
- **Port**: Default Cloud Run `8080` (or `PORT=8000`)
- **Build**: Uses modern Astral `uv` (`uv sync --frozen --no-dev`) without requiring Docker BuildKit `--mount` syntax.
- **Cloud SQL Connection**: Add instance `interview-ready-52479:europe-west1:interview-ready-db` under **Cloud SQL connections**.
- **Environment Variables**:
  - `DATABASE_URL`: `postgresql+asyncpg://<USER>:<URL_ENCODED_PASSWORD>@/interview_ready?host=/cloudsql/<PROJECT>:<REGION>:<INSTANCE>`
  - `REDIS_URL`: `rediss://default:<PASSWORD>@<HOST>.upstash.io:6379` *(Note: Must use `rediss://` with double 's' for TLS encryption)*
  - `WEB_ORIGINS`: `https://interview-ready-webnew-153072465008.europe-west1.run.app` *(plus custom domains)*
  - `APP_ENV`: `production`

#### Frontend (`interview-ready-web`):
- **Dockerfile**: `Dockerfile.web` *(located at repository root to allow build context access to `packages/api-types`)*
- **Port**: `8080`
- **Build**: Standalone Next.js 15 build with output file tracing root at workspace root.
- **Environment Variables**:
  - `NEXT_PUBLIC_API_URL`: URL of your live API (e.g. `https://interview-ready-api-153072465008.europe-west1.run.app`)
  - `NEXT_PUBLIC_FIREBASE_API_KEY`: Real Firebase Web API key
  - `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN`: `interview-ready-52479.firebaseapp.com`
  - `NEXT_PUBLIC_FIREBASE_PROJECT_ID`: `interview-ready-52479`
  - `NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET`: `interview-ready-52479.firebasestorage.app`
  - `NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID`: Your sender ID
  - `NEXT_PUBLIC_FIREBASE_APP_ID`: Your Firebase web app ID

---

## Database Migrations (Cloud SQL)

Database migrations are not executed at container build time (isolated build sandbox). Migrations must be run once against the Cloud SQL database:

1. **Authorized Network (Local Run)**:
   - Temporarily add your public IP address under **Cloud SQL $\rightarrow$ Connections $\rightarrow$ Authorized networks**.
   - Ensure the database `interview_ready` exists in the Cloud SQL instance (`CREATE DATABASE interview_ready;`).
   - Run Alembic:
     ```bash
     cd apps/api
     DATABASE_URL="postgresql+asyncpg://<USER>:<URL_ENCODED_PASS>@<CLOUD_SQL_PUBLIC_IP>:5432/interview_ready" uv run alembic upgrade head
     ```
2. **Password URL-Encoding**:
   - Special characters like `@` in passwords must be URL-encoded (e.g. `@` $\rightarrow$ `%40`).
   - `alembic/env.py` automatically escapes `%` as `%%` to prevent `configparser` interpolation errors.

---

## Authentication & CORS Configuration

### 1. Firebase Authorized Domains
When deploying the frontend to Cloud Run or custom domains, Firebase Auth popups/redirects will fail with `auth/unauthorized-domain` unless whitelisted:
1. Open **Firebase Console $\rightarrow$ Authentication $\rightarrow$ Settings $\rightarrow$ Authorized domains**.
2. Click **"Add domain"** and enter your Cloud Run web hostname:
   - `interview-ready-webnew-153072465008.europe-west1.run.app`
3. If using Google Sign-In, ensure **Google** is enabled under **Authentication $\rightarrow$ Sign-in method** with a project support email.

### 2. Backend CORS Whitelisting
The FastAPI backend validates the `Origin` header against `web_origins`:
- In Cloud Run for `interview-ready-api`, ensure `WEB_ORIGINS` includes your web URL:
  ```text
  WEB_ORIGINS=https://interview-ready-webnew-153072465008.europe-west1.run.app
  ```

---

## Security Invariants

1. **Non-Root Containers**: Both FastAPI and Next.js containers execute as unprivileged users (`appuser:10001` and `nextjs:1001`).
2. **No Baked Secrets**: Container images contain zero credentials or environment secrets.
3. **Cloud SQL Unix Sockets**: Production Cloud Run services connect over secure internal Unix domain sockets (`/cloudsql/...`), avoiding public database IP exposure.
4. **Encrypted Redis**: Upstash Redis is accessed strictly via TLS (`rediss://`).
