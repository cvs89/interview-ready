#!/usr/bin/env bash
# Explicit opt-in: deploy only an already-built API image. Does NOT create a
# database, enable billing, grant IAM, delete Cloud SQL, or run SQL migrations.
set -euo pipefail
: "${GCP_PROJECT_ID:?Set GCP_PROJECT_ID}"
: "${GCP_REGION:?Set GCP_REGION near the selected Firestore location}"
: "${API_IMAGE:?Set a tested immutable API_IMAGE}"
: "${API_SERVICE_ACCOUNT:?Set a least-privilege API service account}"
: "${FIRESTORE_DATABASE_ID:?Set the exact database ID - hosted ID is default without parentheses}"
: "${CONFIRM_FIRESTORE_CUTOVER:?Set to yes after backup, data and index verification}"
if [[ "${CONFIRM_FIRESTORE_CUTOVER}" != "yes" ]]; then
  echo "Cutover not confirmed." >&2
  exit 1
fi
# Existing Redis, LiveKit, authentication, web origins and payment secrets must
# already be configured. Update rather than replace those environment values.
gcloud run deploy interview-ready-api \
  --project="${GCP_PROJECT_ID}" \
  --region="${GCP_REGION}" \
  --image="${API_IMAGE}" \
  --service-account="${API_SERVICE_ACCOUNT}" \
  --clear-cloudsql-instances \
  --remove-secrets=DATABASE_URL \
  --remove-env-vars=DATABASE_URL,FIRESTORE_EMULATOR_HOST \
  --update-env-vars="DATABASE_BACKEND=firestore,FIRESTORE_PROJECT_ID=${GCP_PROJECT_ID},FIRESTORE_DATABASE_ID=${FIRESTORE_DATABASE_ID},APP_ENV=production" \
  --min-instances=0 \
  --max-instances=2 \
  --port=8000
