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

### 3. Deploy via Automated Pipeline
Run the automated deployment script:
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export CLOUD_SQL_INSTANCE="interview-ready-db"

./infrastructure/scripts/deploy.sh
```

---

## Security Invariants

1. **Non-Root Containers**: Both FastAPI and Next.js containers execute as unprivileged users (`appuser:10001` and `nextjs:1001`).
2. **No Baked Secrets**: Container images contain zero credentials or environment secrets.
3. **IAM Least Privilege**: Cloud Run service accounts are granted only:
   - `roles/cloudsql.client`
   - `roles/secretmanager.secretAccessor` (scoped to specific secrets)
   - `roles/storage.objectViewer` / `roles/storage.objectCreator`
4. **Cloud SQL Unix Sockets**: Production Cloud Run services connect over secure internal Unix domain sockets (`/cloudsql/...`), avoiding public database IP exposure.
