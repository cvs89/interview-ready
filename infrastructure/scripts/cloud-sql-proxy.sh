#!/usr/bin/env bash
# ==============================================================================
# Helper to run the Cloud SQL Auth Proxy for local development / testing
# ==============================================================================
set -euo pipefail

: "${GCP_PROJECT_ID:?Environment variable GCP_PROJECT_ID is required}"
: "${GCP_REGION:=us-central1}"
: "${CLOUD_SQL_INSTANCE:?Environment variable CLOUD_SQL_INSTANCE is required}"
: "${LOCAL_PORT:=5432}"

INSTANCE_CONNECTION_NAME="${GCP_PROJECT_ID}:${GCP_REGION}:${CLOUD_SQL_INSTANCE}"

echo "Starting Cloud SQL Auth Proxy for ${INSTANCE_CONNECTION_NAME} on 127.0.0.1:${LOCAL_PORT}..."

if ! command -v cloud-sql-proxy &> /dev/null; then
    echo "cloud-sql-proxy command not found. Installing or download from https://cloud.google.com/sql/docs/postgres/sql-proxy"
    echo "Alternatively run via Docker:"
    echo "docker run --rm -p 127.0.0.1:${LOCAL_PORT}:5432 gcr.io/cloud-sql-connectors/cloud-sql-proxy:latest --address 0.0.0.0 --port 5432 ${INSTANCE_CONNECTION_NAME}"
    exit 1
fi

cloud-sql-proxy --address 127.0.0.1 --port "${LOCAL_PORT}" "${INSTANCE_CONNECTION_NAME}"
