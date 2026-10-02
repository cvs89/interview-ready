# Infrastructure and Deployment Manifests

This directory contains cloud deployment manifests, configuration templates, and operational automation scripts for the Interview Ready platform.

## Directory Structure

```
infrastructure/
├── cloudrun/
│   ├── api-service.yaml       # Cloud Run Service manifest for FastAPI backend
│   ├── web-service.yaml       # Cloud Run Service manifest for Next.js web application
│   └── migration-job.yaml     # Cloud Run Job manifest for one-shot Alembic migrations
└── scripts/
    ├── deploy.sh              # Production build, migration, and service rollout script
    └── cloud-sql-proxy.sh     # Cloud SQL Auth Proxy launcher for local development
```

## Quick Start

### Deploying to Production
```bash
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export CLOUD_SQL_INSTANCE="interview-ready-db"

./infrastructure/scripts/deploy.sh
```

For detailed infrastructure documentation, refer to:
- [Production Deployment Guide](../docs/deployment.md)
- [Environment Variables Reference](../docs/environment-variables.md)
- [Cloud SQL & Pooling Guide](../docs/cloudsql-guide.md)
- [Database Migration Strategy](../docs/migration-guide.md)
