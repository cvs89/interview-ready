# Environment Variables and Secret Configuration Reference

## API Service (`apps/api`)

| Variable | Description | Default / Example | Secret / Plain |
| --- | --- | --- | --- |
| `APP_NAME` | Service display name | `Interview Ready API` | Plain |
| `APP_ENV` | Runtime environment (`development`, `test`, `staging`, `production`) | `development` | Plain |
| `LOG_LEVEL` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` | Plain |
| `DATABASE_URL` | PostgreSQL connection string (asyncpg driver). For Cloud Run via Unix socket: `postgresql+asyncpg://<USER>:<PASS>@/interview_ready?host=/cloudsql/<PROJECT>:<REGION>:<INSTANCE>` | `postgresql+asyncpg://...` | **Secret** |
| `REDIS_URL` | Redis connection URL. For Upstash: Must use TLS scheme `rediss://default:<PASS>@<HOST>:6379` | `rediss://...` | **Secret** |
| `WEB_ORIGINS` | Allowed CORS origins (comma-separated or JSON list). Include your Cloud Run Web URL: `https://interview-ready-webnew-153072465008.europe-west1.run.app` | `http://localhost:3000` | Plain |
| `RESERVATION_TTL_MINUTES` | Temporary slot reservation expiry window | `10` | Plain |
| `WEBHOOK_SIGNING_SECRET` | Secret key for verifying payment provider HMAC signatures | `local_dev_secret` | **Secret** |
| `PAYMENT_PROVIDER` | Active payment processor implementation (`mock`, `stripe`, `razorpay`) | `mock` | Plain |
| `DESKTOP_TICKET_TTL_SECONDS`| Lifetime of one-time desktop authentication ticket in Redis | `60` | Plain |
| `JOIN_WINDOW_LEAD_MINUTES` | Time before slot start when room join becomes permissible | `10` | Plain |
| `JOIN_WINDOW_GRACE_MINUTES`| Time after slot end before room join access is revoked | `30` | Plain |
| `SESSION_JWT_SECRET` | 256-bit secret key used to sign `Session JWT` for room participants | `...` | **Secret** |
| `SESSION_JWT_TTL_SECONDS` | Lifetime of Session JWT (default 2 hours) | `7200` | Plain |
| `LIVEKIT_URL` | WebRTC LiveKit server WebSocket endpoint | `wss://livekit.example.com` | **Secret** |
| `LIVEKIT_API_KEY` | LiveKit server authentication key | `...` | **Secret** |
| `LIVEKIT_API_SECRET` | LiveKit server API signing secret | `...` | **Secret** |
| `LIVEKIT_TOKEN_TTL_SECONDS` | Room access token TTL | `7200` | Plain |
| `DB_POOL_SIZE` | SQLAlchemy connection pool size per container replica | `5` | Plain |
| `DB_MAX_OVERFLOW` | Maximum surge connections permitted per replica | `10` | Plain |
| `DB_POOL_TIMEOUT` | Seconds to wait for an available DB connection from pool | `30` | Plain |
| `DB_POOL_RECYCLE` | Maximum seconds before an idle connection is recycled | `1800` | Plain |
| `DB_POOL_PRE_PING` | Test connections with a ping query prior to checkout | `true` | Plain |
| `GCP_PROJECT_ID` | Google Cloud project identifier | `...` | Plain |
| `GCS_BUCKET_NAME` | Cloud Storage bucket for file uploads | `...` | Plain |
| `GCS_SIGNED_URL_TTL_SECONDS`| Duration for generated upload/download signed URLs | `3600` | Plain |

---

## Web Frontend Service (`apps/web`)

| Variable | Description | Default / Example | Secret / Plain |
| --- | --- | --- | --- |
| `NODE_ENV` | Node runtime environment | `production` | Plain |
| `PORT` | Web server listening port | `3000` | Plain |
| `NEXT_PUBLIC_API_URL` | Public API base endpoint accessed by browser | `https://yourdomain.com/api` | Plain |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Firebase Web Client API Key | `AIzaSy...` | Plain |
| `NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN` | Firebase Web Auth Domain | `project.firebaseapp.com` | Plain |
| `NEXT_PUBLIC_FIREBASE_PROJECT_ID` | Firebase Project ID | `project-id` | Plain |
| `NEXT_TELEMETRY_DISABLED` | Disables Next.js anonymous analytics collection | `1` | Plain |

---

## Desktop Application (`apps/desktop`)

| Variable | Description | Default / Example | Secret / Plain |
| --- | --- | --- | --- |
| `VITE_API_BASE_URL` | Default fallback API endpoint if not overridden by deep link | `http://localhost:8000` | Plain |
