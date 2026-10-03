#!/usr/bin/env bash
# ==============================================================================
# Interview Ready — Automated Production Deployment Script
# ==============================================================================
set -euo pipefail

# Required Environment Variables
: "${GCP_PROJECT_ID:?Environment variable GCP_PROJECT_ID is required}"
: "${GCP_REGION:=us-central1}"
: "${CLOUD_SQL_INSTANCE:?Environment variable CLOUD_SQL_INSTANCE is required}"
: "${FIREBASE_PROJECT_ID:=${GCP_PROJECT_ID}}"

IMAGE_REGISTRY="${GCP_REGION}-docker.pkg.dev/${GCP_PROJECT_ID}/interview-ready"
API_IMAGE="${IMAGE_REGISTRY}/api:${GITHUB_SHA:-latest}"
WEB_IMAGE="${IMAGE_REGISTRY}/web:${GITHUB_SHA:-latest}"

echo "=========================================================================="
echo "🚀 Deploying Interview Ready to GCP (Project: ${GCP_PROJECT_ID})"
echo "=========================================================================="

# 1. Build and push API Docker image
echo "📦 Building and pushing FastAPI Docker image..."
docker build -t "${API_IMAGE}" -t "${IMAGE_REGISTRY}/api:latest" -f apps/api/Dockerfile apps/api
docker push "${API_IMAGE}"
docker push "${IMAGE_REGISTRY}/api:latest"

# 2. Build and push Next.js Web Docker image
echo "📦 Building and pushing Next.js Web Docker image..."
docker build -t "${WEB_IMAGE}" -t "${IMAGE_REGISTRY}/web:latest" -f Dockerfile.web .
docker push "${WEB_IMAGE}"
docker push "${IMAGE_REGISTRY}/web:latest"

# 3. Execute Database Migrations via Cloud Run Job (Single execution guarantee)
echo "🗄️ Executing Alembic database schema migrations via Cloud Run Job..."
gcloud run jobs deploy interview-ready-migrations \
  --image="${API_IMAGE}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --set-cloudsql-instances="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUD_SQL_INSTANCE}" \
  --command="alembic" \
  --args="upgrade,head" \
  --set-secrets="DATABASE_URL=interview-ready-database-url:latest" \
  --quiet

echo "⏳ Running migration job and waiting for completion..."
gcloud run jobs execute interview-ready-migrations \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --wait

# 4. Deploy API Cloud Run Service
echo "🌐 Deploying FastAPI backend service to Cloud Run..."
gcloud run deploy interview-ready-api \
  --image="${API_IMAGE}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --platform=managed \
  --allow-unauthenticated \
  --set-cloudsql-instances="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUD_SQL_INSTANCE}" \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=80 \
  --cpu=1 \
  --memory=1024Mi \
  --set-env-vars="APP_ENV=production,LOG_LEVEL=INFO,DB_POOL_SIZE=5,DB_MAX_OVERFLOW=10,DB_POOL_TIMEOUT=30,DB_POOL_RECYCLE=1800,DB_POOL_PRE_PING=true" \
  --set-secrets="DATABASE_URL=interview-ready-database-url:latest,REDIS_URL=interview-ready-redis-url:latest,SESSION_JWT_SECRET=interview-ready-session-jwt-secret:latest,WEBHOOK_SIGNING_SECRET=interview-ready-webhook-signing-secret:latest,LIVEKIT_API_KEY=interview-ready-livekit-api-key:latest,LIVEKIT_API_SECRET=interview-ready-livekit-api-secret:latest,LIVEKIT_URL=interview-ready-livekit-url:latest" \
  --quiet

# 5. Deploy Web Cloud Run Service
echo "🌐 Deploying Next.js frontend service to Cloud Run..."
gcloud run deploy interview-ready-web \
  --image="${WEB_IMAGE}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=1 \
  --max-instances=20 \
  --concurrency=100 \
  --cpu=1 \
  --memory=1024Mi \
  --port=3000 \
  --set-env-vars="NODE_ENV=production,NEXT_TELEMETRY_DISABLED=1" \
  --quiet

# 6. Deploy Firebase Hosting (Routes static assets and redirects to Cloud Run)
echo "🔥 Deploying Firebase Hosting with Cloud Run rewrites..."
firebase deploy --only hosting --project="${FIREBASE_PROJECT_ID}"

echo "=========================================================================="
echo "✅ Deployment completed successfully!"
echo "=========================================================================="
