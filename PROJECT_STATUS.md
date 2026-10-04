# Interview Ready — Project Status and AI Handoff

## Competitor research — 4 October 2026

- Public-offering research: [Competitor report](docs/COMPETITOR_RESEARCH_2026-10-04.md).
- Identified 13 relevant platforms: five direct human-mock competitors, four adjacent mentoring/booking platforms, and four AI/self-study alternatives. This is a shortlist, not an exhaustive market count; actual bookings were not tested.
- Important corrections: Aced includes former Exponent/Pramp branding; Hello Interview ended live mocks and mentorship on 31 May 2026.
- Pending research: like-for-like pricing/availability comparison, candidate/interviewer interviews, and a small paid pilot.
- Documentation only; implementation and design-completion statuses are unchanged.

## Design Implementation — The Confidence Club (Complete)

- **Selected Direction**: **Direction 04 — The Confidence Club** (Approved by user).
- **Status**: **Complete**.
- **Palette**: Primary Terracotta `#9B3B25` (hover `#83321F`, active `#6D2919`, subtle `#FBF2ED`), Background Ivory `#FFF8F0` (warm `#FFFDFB`, card `#FFFFFF`), Accent Peach `#F8DDC9` (subtle `#FDF5EE`, border `#ECC2A4`), Ink `#342523` (muted `#6E5652`, subtle `#96817D`, border `#EADBCE`).
- **Typography**: Lora (editorial serif headings) + DM Sans (interface and body sans-serif).
- **Shape Language**: 24px rounded cards (`rounded-[24px]` / `rounded-[20px]`), pill-shaped action buttons (`rounded-full`), warm restrained elevation, rounded-xl inputs.
- **Completed Components & Screens**:
  1. **Design Tokens & Typography Foundation**:
     - `apps/web/src/app/globals.css`: Tailwind v4 theme variables, `.card-confidence`, `.btn-pill-primary`, `.btn-pill-secondary`, `.badge-confidence-*`, Google Fonts `@import`.
     - `apps/web/src/app/layout.tsx`: RootLayout configured with Ivory background `#FFF8F0`, Ink `#342523`, and DM Sans typography.
     - `apps/desktop/src/styles.css`: CSS theme variables for Confidence Club palette, serif/sans utility classes.
  2. **Navigation & Shared Components**:
     - `apps/web/src/components/Navbar.tsx`: Warm ivory glassmorphism navbar, editorial logo `interview ready.`, pill actions, responsive mobile menu.
     - `apps/web/src/components/marketplace/InterviewerCard.tsx`: 24px cards, initials avatar in peach circle, pill skill tags, terracotta CTA.
     - `apps/web/src/components/marketplace/InterviewerFilter.tsx`: Warm card, terracotta focus rings, pill reset.
     - `apps/web/src/components/marketplace/SlotSelector.tsx`: Reservation banner, selected slot highlights, pill action buttons.
     - `apps/web/src/components/booking/ReservationTimer.tsx`: Pill countdown badge with tabular figures and urgent/expired states.
     - `apps/web/src/components/booking/PaymentStatusPoller.tsx`: Poller, confirmed state with exact test string ("Payment webhook confirmation received. Your mock interview slot is booked and secured."), error states.
     - `apps/web/src/components/dashboard/BookingList.tsx`: Tabbed filters, 24px session cards, warm badges.
     - `apps/web/src/components/dashboard/JoinCallCard.tsx`: Warm card, status badges, countdown, join action.
     - `apps/web/src/components/dashboard/DesktopFallbackModal.tsx`: 24px modal, OS download pills, retry action.
  3. **Web Pages Redesigned**:
     - Homepage (`apps/web/src/app/page.tsx`): Hero with warm typography, stats, 3-step path, verified pillars, interviewer CTA, FAQ accordion.
     - Sign In (`apps/web/src/app/auth/sign-in/page.tsx`): 24px card, peach icon circle, Lora heading, warm inputs, pill submit and Google button.
     - Sign Up (`apps/web/src/app/auth/sign-up/page.tsx`): 24px card, peach icon circle, Lora heading, warm inputs, pill submit and Google button.
     - Interviewer Auth (`apps/web/src/app/auth/interviewer/page.tsx`): Editorial headline, value props with warm chips, 24px card, role switcher tabs, pill CTA.
     - Marketplace & Discovery (`apps/web/src/app/marketplace/page.tsx`): Editorial header, sidebar filter, responsive grid of interviewer cards.
     - Interviewer Profile & Booking (`apps/web/src/app/interviewers/[id]/page.tsx`): Profile header card, verified check, pill skill chips, rate card, Lora headings, slot container.
     - Booking Confirmation (`apps/web/src/app/bookings/[id]/confirmation/page.tsx`): Warm container wrapping `PaymentStatusPoller`.
     - Candidate Dashboard (`apps/web/src/app/dashboard/page.tsx`): Welcome banner, role chip, pill refresh, pill "Book New Slot", `BookingList`, `JoinCallCard`.
     - Interviewer Workspace & Profile Manager (`apps/web/src/app/interviewer/page.tsx`): Verification status chips, AI auto-fill banner, 24px cards, tabs for Profile, Skills, Slots, Bookings.
     - Admin Portal (`apps/web/src/app/admin/layout.tsx`, `page.tsx`, `users/page.tsx`, `verifications/page.tsx`, `bookings/page.tsx`, `audit-logs/page.tsx`): Shield badges, operations cards, 24px tables, modal dialogs with terracotta accents.
  4. **Desktop App**:
     - Device Preview (`apps/desktop/src/components/DevicePreview.tsx`): 28px card, Lora header, high-contrast video preview, pill join/cancel buttons.
     - Deep Link Launch Prompt (`apps/desktop/src/components/DeepLinkPrompt.tsx`): 28px card, peach icon container, Lora heading, warm input, pill button.
     - Error Display (`apps/desktop/src/components/ErrorDisplay.tsx`): 28px card, warm red alert container, pill retry/return buttons.
     - Live Interview Room (`apps/desktop/src/components/LiveRoom.tsx`): Clean warm header with LiveKit room indicator, role pill badge, WebRTC status, dark focused video stage (`#1E1715` / `#140E0C`), floating rounded-full control bar with terracotta Leave pill, role-isolated 60% interviewer workspace (Evaluation Rubric 1-5 rating pills, private notes with confidential warning, shared scratchpad) and candidate scratchpad.
- **Verification Checks & Results**:
  - Web Unit & Component Tests: 40/40 passing (`npm run test:web`).
  - Desktop Unit & Component Tests: 15/15 passing (`npm run test:desktop`).
  - Web TypeScript Typecheck: Passed with 0 errors (`npm run typecheck:web`).
  - Desktop TypeScript Typecheck: Passed with 0 errors (`npm run typecheck:desktop`).
  - Next.js Production Build: 16/16 routes compiled successfully (`npm run build:web`).
- **Files Changed**:
  - `apps/web/src/app/globals.css`, `layout.tsx`, `page.tsx`, `marketplace/page.tsx`, `auth/sign-in/page.tsx`, `auth/sign-up/page.tsx`, `auth/interviewer/page.tsx`, `interviewers/[id]/page.tsx`, `bookings/[id]/confirmation/page.tsx`, `dashboard/page.tsx`, `interviewer/page.tsx`, `admin/layout.tsx`, `admin/page.tsx`, `admin/users/page.tsx`, `admin/verifications/page.tsx`, `admin/bookings/page.tsx`, `admin/audit-logs/page.tsx`.
  - `apps/web/src/components/Navbar.tsx`, `marketplace/InterviewerCard.tsx`, `marketplace/InterviewerFilter.tsx`, `marketplace/SlotSelector.tsx`, `booking/ReservationTimer.tsx`, `booking/PaymentStatusPoller.tsx`, `dashboard/BookingList.tsx`, `dashboard/JoinCallCard.tsx`, `dashboard/DesktopFallbackModal.tsx`.
  - `apps/desktop/src/styles.css`, `components/DevicePreview.tsx`, `components/DeepLinkPrompt.tsx`, `components/ErrorDisplay.tsx`, `components/LiveRoom.tsx`.
- **Blockers**: None.

Last updated: 2026-10-04 (Asia/Kolkata)

This file is the durable implementation tracker for humans and AI tools. Update it at the end of every module. The numbered prompt files in `interview-ready-codex-prompts/` remain the source of truth for requirements.

## Current position

- Completed through: **Module 13**
- Next module: **Module 14 — Concurrency, Load, Integration, and End-to-End Validation**
- Next prompt: `interview-ready-codex-prompts/14_CONCURRENCY_LOAD_INTEGRATION_AND_E2E.md`
- Overall progress: **13 of 15 implementation modules complete**
- Repository state: initialized on `main` branch with remote origin `https://github.com/cvs89/interview-ready.git`

## Module checklist

| Module | Status | Summary |
| --- | --- | --- |
| 01 — Repository Foundation | Complete | Monorepo, FastAPI, Next.js 15, Tauri v2 shell, shared packages, local Compose services, CI foundation, health checks, logging and error envelope. |
| 02 — Database Schema, Alembic, Firebase Authentication, RBAC | Complete | Identity schema, Firebase token verification, candidate auto-registration, `/auth/me`, RBAC, ownership and verified-email helpers. |
| 03 — Interviewer Profiles, Verification State, Availability Slots | Complete | Profiles, skills, admin verification, UTC slots, ownership enforcement, public discovery, and PostgreSQL overlap exclusion constraint. |
| 04 — Slot Reservation, Booking, Payment, Webhook Confirmation | Complete | Race-safe slot reservation with row locking and TTL, snapshot pricing, abstract payment provider with mock HMAC verification, webhook deduplication and booking confirmation, expiry worker, and cancellation/refund state transitions. |
| 05 — Desktop Authentication Ticket, Session JWT, LiveKit | Complete | Redis-backed single-use 256-bit desktop tickets with SHA-256 keying and atomic GETDEL consumption, join window validation with lead and grace periods, `InterviewSession` lifecycle, dedicated Session JWT signing, and room-scoped LiveKit access tokens. |
| 06 — Next.js Web Authentication and Interviewer Marketplace | Complete | Next.js 15 App Router web marketplace with Firebase Web Auth integration, dynamic AuthContext with `/auth/me` sync, typed ApiClient with auto-refresh token header injection, public interviewer discovery with filter controls, slot selection with 10-minute reservation countdown, checkout dispatch, and webhook-driven payment confirmation polling. |
| 07 — Web Booking Dashboard and Join Call Experience | Complete | Candidate and interviewer booking hub with tabbed statuses (upcoming, completed, cancelled/expired), live join window countdown and polling, secure one-time ticket minting, protocol deep link launch (`interviewapp://join`), and desktop fallback modal with retry minting and OS download links. |
| 08 — Tauri v2 Desktop Deep Link and Live Interview Room | Complete | Tauri v2 `interviewapp://` protocol scheme and strict CSP, zero-log deep-link parser and ticket exchange, in-memory ephemeral session state, device preview/check-in, WebRTC/LiveKit video controls, and role-isolated split layout (interviewer 40/60 video/rubric/notes workspace vs candidate video + shared scratchpad). |
| 09 — Rubric, Feedback, Notes, Reviews | Complete | Structured interview rubric drafting & submission, transactional booking completion (`COMPLETED`) and session closure (`ENDED`), confidential private interviewer notes isolation from candidates, verified candidate-only post-completion interviewer reviews with 1-5 rating constraints, and aggregate rating summaries. |
| 10 — Notifications, Durable Jobs, Audit Trail | Complete | Durable background task processing abstractions (Cloud Tasks / job processor), multi-channel notifications (Email, FCM, in-app notification center) with deduplication and idempotency keys, operational audit trail with secret redaction, reminder scanning (24h, 1h, 10m), and admin audit log query API. |
| 11 — Admin Portal and Operational Controls | Complete | Safe administrative operations portal in Next.js 15 with role guard, user management with `ACTIVE`/`SUSPENDED`/`DISABLED` state controls & self-suspension protections, interviewer verification review queue, full booking & payment inspection, immutable audit logging with credential exclusion, and strict admin RBAC. |
| 12 — Production Docker, Cloud Run, Firebase Hosting, Cloud SQL, Secrets | Complete | Multi-stage production Dockerfiles for FastAPI & Next.js standalone, Firebase Hosting with Cloud Run rewrites, Cloud SQL Unix domain socket support with configurable pooling, Secret Manager architecture, Cloud Run Job migration strategy, and deployment scripts/docs. |
| 13 — CI/CD, Quality Gates, Security Baseline | Complete | Comprehensive GitHub Actions PR & Deployment pipelines, edge & application security headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Permissions-Policy), sliding window rate limiting primitives (ticket mint/exchange, reservations, checkout, search), and desktop release guards. |
| 14 — Concurrency, Load, Integration, and End-to-End Validation | **Next** | Not started. |
| 15 — Final Production Readiness Review | Pending | Not started. |

## Completed implementation details

### Module 01

- Async FastAPI application factory with structured logging and request IDs.
- `/health/live` and dependency-aware `/health/ready` endpoints.
- Async SQLAlchemy engine/session and Redis client factories.
- Central API error envelope.
- Next.js 15 App Router application with strict TypeScript, Tailwind, Lucide, environment validation, tests, and a health route.
- Tauri v2 React/TypeScript shell with a restrictive CSP and only `core:default` permissions.
- Root npm workspaces, Docker Compose for PostgreSQL/Redis, environment examples, documentation, and CI workflow.

### Module 02

- Models: `User`, `InterviewerProfile`, `Skill`, and `InterviewerSkill`.
- Alembic revision `20261002_0001` creates the identity schema and `user_role` enum.
- Firebase Admin token verification uses `check_revoked=True` and handles invalid, revoked, expired, and disabled identities.
- New identities are registered as `CANDIDATE`; token claims never control application roles.
- Repeated login updates safe metadata without duplicating users or overwriting roles.
- Reusable `get_current_user`, `require_role`, `require_verified_email`, and ownership guard.
- Authenticated `GET /auth/me` endpoint.

### Module 03

- Models: `InterviewerVerification` and `AvailabilitySlot`.
- Alembic revision `20261002_0002` creates verification/availability enums and tables.
- PostgreSQL `btree_gist` plus `tstzrange` exclusion constraint prevents overlapping slots for one interviewer.
- `UTCDateTime` SQLAlchemy type normalizes aware timestamps to UTC, including under SQLite tests.
- Candidate users may submit an interviewer profile; only admin approval promotes them to `INTERVIEWER` and enables slots.
- Interviewers can update profiles/pricing, manage normalized skills, and create/update/block owned slots.
- Admins can create skills and approve/reject verification applications.
- Public discovery filters by skill, experience, slot price, and availability range.
- Public responses exclude email, Firebase UID, reviewer identity, and verification notes.
- Public slot APIs expose only `AVAILABLE` slots.

### Module 04

- Models: `Booking`, `Payment`, and `PaymentWebhookEvent`.
- Alembic revision `20261002_0003` creates `booking_status` and `payment_status` enums, `bookings`, `payments`, and `payment_webhook_events` tables with constraints and indexes.
- Race-safe reservation transaction: locks row using `SELECT ... FOR UPDATE`, normalizes expired reservations back to `AVAILABLE`, verifies slot availability and future time, prevents self-booking, snapshots `price_minor` and `currency`, and sets a configurable 10-minute reservation TTL.
- Abstract `PaymentProvider` interface with `MockPaymentProvider` utilizing HMAC SHA-256 webhook signatures.
- Checkout endpoint `POST /api/v1/payments/{booking_id}/checkout` enforcing booking ownership, non-expired reservation, and database-driven price snapshot.
- Webhook endpoint `POST /api/v1/webhooks/payments/{provider}` with signature verification, event deduplication by `provider_event_id`, row locking, price/currency snapshot verification, marking payment `PAID`, booking `CONFIRMED`, slot `BOOKED`, and clearing reservation metadata.
- Periodic / durable reservation expiry worker in `app/workers/reservation_expiry.py` and service `expire_stale_reservations` resetting expired slots to `AVAILABLE` and pending bookings to `EXPIRED`.
- Cancellation and refund state transitions and service hooks.

### Module 05

- Models: `InterviewSession` with `SessionStatus` enum (`READY`, `ACTIVE`, `ENDED`) and unique constraint on opaque random LiveKit room names.
- Alembic revision `20261002_0004` creates `session_status` enum and `interview_sessions` table with foreign key to `bookings.id`.
- Redis-backed desktop authentication ticket: mints 256-bit cryptographically secure tickets keyed in Redis by `sha256(ticket)` with 60-second TTL.
- Ticket exchange endpoint `POST /api/v1/auth/exchange-desktop-ticket` using atomic Redis `GETDEL` (and Lua fallback) guaranteeing strictly one-time consumption.
- Join window backend calculation from slot times with 10-minute lead window and 30-minute grace window.
- Session JWT generator with dedicated signing secret and claims (`sub`, `booking_id`, `session_id`, `role`, `user_role`, `email`, `name`, `iat`, `exp`, `jti`).
- LiveKit room token generator scoped strictly to the session's opaque room name with publishing/subscribing video grants.
- Join-status endpoint `GET /api/v1/bookings/{booking_id}/join-status`.
- Dual participant join tracking promoting session to `ACTIVE` and booking to `IN_PROGRESS`.

### Module 06

- Shared TypeScript domain models in `packages/api-types` (`User`, `InterviewerProfile`, `Skill`, `AvailabilitySlot`, `Booking`, `PaymentCheckoutResponse`, `JoinStatusResponse`).
- Firebase Web SDK client initialization in `apps/web/src/lib/firebase.ts`.
- Typed `ApiClient` in `apps/web/src/lib/api-client.ts` with automatic fresh Firebase ID token injection via `getIdToken()`, typed `ApiError` envelope parsing, and currency/timezone helpers (`formatCurrency`, `formatUtcToLocal`, `calculateDurationMinutes`).
- Reactive `AuthContext` (`apps/web/src/context/AuthContext.tsx`) managing Firebase Auth lifecycle (Google popup, email/password signup/signin, logout) and syncing user data from `/auth/me`.
- Global responsive `Navbar` (`apps/web/src/components/Navbar.tsx`) with dynamic authentication state and navigation links.
- Interviewer marketplace discovery (`apps/web/src/app/marketplace/page.tsx`) with multi-facet filters (`InterviewerFilter`), grid view (`InterviewerCard`), and pagination.
- Interviewer profile and slot booking detail view (`apps/web/src/app/interviewers/[id]/page.tsx` and `SlotSelector.tsx`) featuring 10-minute temporary reservation calls to `POST /api/v1/bookings/reserve`, visual countdown timer (`ReservationTimer.tsx`), 409 conflict handling, and seamless checkout redirection.
- Payment confirmation status polling page (`apps/web/src/app/bookings/[id]/confirmation/page.tsx` and `PaymentStatusPoller.tsx`) querying backend `/api/v1/bookings/{id}` until verified `CONFIRMED` status is established by webhook.
- Candidate dashboard (`apps/web/src/app/dashboard/page.tsx`) displaying upcoming and past mock interview bookings with join call actions.

### Module 07

- Enhanced shared API types with `MintDesktopTicketRequest` and `MintDesktopTicketResponse` in `packages/api-types`.
- `DesktopFallbackModal` (`apps/web/src/components/dashboard/DesktopFallbackModal.tsx`) with browser protocol guidance, direct download links for Windows, macOS, and Linux, and a retry button that mints fresh tickets.
- `JoinCallCard` (`apps/web/src/components/dashboard/JoinCallCard.tsx`) with real-time countdown timer, automatic join-status polling from `GET /api/v1/bookings/{id}/join-status`, strict `can_join` guard on the action button, safe deep link dispatch (`interviewapp://join?ticket=...&bookingId=...`), zero console/storage ticket persistence, and automatic fallback modal invocation.
- `BookingList` (`apps/web/src/components/dashboard/BookingList.tsx`) with tabbed organization (Upcoming, Completed, Cancelled / Expired), candidate-safe details, and contextual action buttons.
- `DashboardPage` (`apps/web/src/app/dashboard/page.tsx`) updated to support both candidate and interviewer views with role-aware headers and refresh controls.

### Module 08

- Tauri v2 `interviewapp://` custom protocol scheme registered with strict CSP in `apps/desktop/src-tauri/tauri.conf.json`.
- `deeplink.ts` (`apps/desktop/src/lib/deeplink.ts`) implements secure deep-link parsing (`parseDeepLinkUrl`) and backend ticket exchange (`exchangeTicket` with `POST /api/v1/auth/exchange-desktop-ticket`) with zero ticket logging or plaintext storage.
- `DevicePreview` (`apps/desktop/src/components/DevicePreview.tsx`) supporting camera/mic check-in, media track control, device permission handling, and role-badged room metadata.
- `LiveRoom` (`apps/desktop/src/components/LiveRoom.tsx`) supporting:
  - WebRTC connection state and reconnection controls.
  - Video tile grid for remote and local participants with mic/camera toggle controls.
  - **Interviewer layout (40% video / 60% workspace)**: Tabbed evaluation workspace featuring a 1-5 star criteria rubric (Problem Solving, System Architecture, Code Quality, Communication), feedback notepad, confidential private notes editor, and shared scratchpad.
  - **Candidate layout**: Video-centric layout with shared code scratchpad, strictly isolating and hiding interviewer rubrics and private notes.
- `ErrorDisplay` (`apps/desktop/src/components/ErrorDisplay.tsx`) handling expired tickets, closed join windows, and network failures with retry workflows.
- `App` (`apps/desktop/src/main.tsx`) coordinating cold start and runtime deep link events, immediate ticket purge, and transition state machine.

### Module 09

- Models: `InterviewRubric` (with `RubricStatus` enum: `DRAFT`, `SUBMITTED`, `LOCKED`, 1-5 score check constraints, versioning, timestamps) and `InterviewerReview` (1-5 rating check constraint, uniqueness on `booking_id`).
- Alembic revision `20261002_0005` creates `rubric_status` enum, `interview_rubrics`, and `interviewer_reviews` tables with constraints, indexes, foreign keys, and cascades.
- Repositories: `RubricRepository` and `ReviewRepository` in `apps/api/app/repositories/feedback.py`.
- Services:
  - `RubricService` (`apps/api/app/services/feedback.py`):
    - `save_draft`: Allows only assigned interviewer to save incremental rubric drafts and increments version.
    - `submit_rubric`: Explicit transaction that verifies interviewer assignment, locks row, sets `status=SUBMITTED`, records `submitted_at`, atomically transitions `Booking` to `COMPLETED` (`completed_at = now`), and ends active `InterviewSession` (`status=ENDED`, `ended_at = now`). Enforces immutability once submitted.
    - `get_interviewer_rubric`: Exposes full rubric including `private_interviewer_notes` only to assigned interviewer and admins.
    - `get_candidate_feedback`: Exposes candidate-safe evaluation (`CandidateFeedbackResponse`) strictly excluding confidential `private_interviewer_notes`, only when rubric is submitted/locked.
  - `ReviewService` (`apps/api/app/services/feedback.py`):
    - `create_review`: Validates candidate identity, confirms booking is in `COMPLETED` state, enforces 1-5 rating check, prevents duplicate reviews (one per booking), and records review.
    - `get_interviewer_rating_summary`: Computes aggregate average rating and review counts.
    - `list_interviewer_reviews`: Lists paginated candidate reviews.
- API Endpoints:
  - `POST /api/v1/bookings/{booking_id}/rubric/draft`
  - `POST /api/v1/bookings/{booking_id}/rubric/submit`
  - `GET /api/v1/bookings/{booking_id}/rubric`
  - `GET /api/v1/bookings/{booking_id}/feedback`
  - `POST /api/v1/bookings/{booking_id}/review`
  - `GET /api/v1/interviewers/{interviewer_id}/rating`
  - `GET /api/v1/interviewers/{interviewer_id}/reviews`
- Shared Types: Updated `packages/api-types` with `RubricStatus`, `RubricDraftRequest`, `RubricSubmitRequest`, `InterviewerRubricResponse`, `CandidateFeedbackResponse`, `ReviewCreateRequest`, `ReviewResponse`, and `InterviewerRatingSummary`.

### Module 10

- Models: `AuditLog`, `InAppNotification`, and `NotificationDeliveryLog`.
- Alembic revision `20261002_0006` creates `audit_logs`, `in_app_notifications`, and `notification_delivery_logs` tables with constraints, indexes, foreign keys, and JSONB payloads.
- Background Tasks & Job Processor (`app/services/tasks.py` and `app/api/tasks.py`):
  - Abstract task runner supporting `expire_reservations`, `send_reminders`, `dispatch_notification`, and `post_interview_reminders`.
  - Scans and enqueues reminder notifications across 24-hour (`REMINDER_24H`), 1-hour (`REMINDER_1H`), and 10-minute (`REMINDER_10M`) windows.
  - Idempotent task execution safe for retries without duplicating state mutations.
- Multi-Channel Notification Service (`app/services/notification.py`):
  - Interface-backed channels (`EmailNotificationChannel`, `FCMNotificationChannel`, `InAppNotificationChannel`).
  - Strict deduplication using database delivery logs keyed by `{event_type}:{channel}:{reference_id}:{recipient_id}`.
  - In-app notification center with read-state tracking, individual read marks, and batch mark-all-read.
- Operational Audit Trail (`app/services/audit.py` and `app/api/audit.py`):
  - Automatic event logging with sensitive token/secret/password metadata redaction (`sanitize_metadata`).
  - Integrated hooks across slot mutations, verification status reviews, booking reservations, payment confirmations, webhook events, cancellations, refunds, rubric submissions, and candidate reviews.
  - Admin-only audit log query API with multi-field filtering (`resource_type`, `resource_id`, `actor_user_id`, `event_type`).
- API Endpoints:
  - `GET /api/v1/notifications/me` — List user's in-app notifications
  - `PATCH /api/v1/notifications/{notification_id}/read` — Mark notification read
  - `POST /api/v1/notifications/read-all` — Mark all user notifications read
  - `POST /api/v1/internal/tasks/process` — Durable tasks worker execution endpoint
  - `GET /api/v1/admin/audit-logs` — Admin audit log query endpoint
- Shared Types: Updated `packages/api-types` with `InAppNotificationResponse`, `AuditLogResponse`, `TaskProcessRequest`, and `TaskProcessResponse`.

### Module 11

- Models & Schema:
  - Added `UserStatus` enum (`ACTIVE`, `SUSPENDED`, `DISABLED`) and indexed `status` column on `User` model.
  - Alembic revision `20261002_0007` creates `user_status` enum and adds `status` column to `users` table with server default `ACTIVE`.
  - Enforced account status checking during authentication & request validation (`ACCOUNT_SUSPENDED`, `ACCOUNT_DISABLED` 403 responses).
- Repositories & Services (`app/repositories/users.py`, `app/repositories/interviewers.py`, `app/repositories/bookings.py`, `app/services/admin.py`):
  - `UserRepository`: Search & filter users by name/email, role, status with pagination; user status mutations.
  - `InterviewerRepository`: Admin verification queue query with status filters (`PENDING`, `IN_REVIEW`, `APPROVED`, `REJECTED`), slot inspection query.
  - `BookingRepository`: Admin inspection of all bookings with participant and slot/payment joins; payment record inspection query.
  - `AdminService`: Coordinated management layer auditing every status mutation (`ADMIN_USER_STATUS_UPDATED`), preventing self-suspension/disabling by active admins (`CANNOT_DISABLE_SELF`), and sanitizing sensitive credentials.
- API Endpoints (`app/api/admin.py`):
  - `GET /api/v1/admin/users` — List/search users with pagination & role/status filters
  - `GET /api/v1/admin/users/{user_id}` — Inspect specific user details
  - `PATCH /api/v1/admin/users/{user_id}/status` — Update user status with audit logging
  - `GET /api/v1/admin/verifications` — Interviewer verification queue
  - `GET /api/v1/admin/bookings` — Marketplace bookings inspection with participant & payment joins
  - `GET /api/v1/admin/bookings/{booking_id}` — Single booking inspection
  - `GET /api/v1/admin/payments` — Payment records inspection
  - `GET /api/v1/admin/slots` — Availability slots inspection
  - `GET /api/v1/admin/audit-logs` — Immutable system audit log inspection
- Web UI (`apps/web/src/app/admin/`):
  - Role-guarded `AdminLayout` checking `apiUser.role === 'ADMIN'` with responsive tab navigation.
  - Admin Overview (`/admin`) displaying live metrics (registered users, pending verifications, bookings count) and safety guidance.
  - User Management (`/admin/users`) with query search, role/status filters, pagination, and status modification modal.
  - Verification Queue (`/admin/verifications`) with review dialog (Approve/Reject + feedback notes).
  - Bookings Inspection (`/admin/bookings`) with status filter, participant details, and detail drawer.
  - Audit Trail (`/admin/audit-logs`) with expandable JSON payloads.
  - Navbar updated to surface Admin Portal link to authenticated administrators.
- Shared Types: Updated `packages/api-types` with `UserStatus`, `AdminUserResponse`, `AdminUserListResponse`, `AdminUserStatusUpdateRequest`, `AdminInterviewerVerificationResponse`, `AdminVerificationListResponse`, `AdminBookingItemResponse`, `AdminBookingListResponse`, `AdminPaymentItemResponse`, `AdminPaymentListResponse`, `AdminSlotItemResponse`, and `AdminSlotListResponse`.

### Module 12

- **FastAPI Production Dockerfile ([`apps/api/Dockerfile`](file:///Users/chandraveerrathore/projects/interview-ready/apps/api/Dockerfile))**:
  - Multi-stage image using pinned `python:3.12-slim` base and `uv` layer caching.
  - Non-root runtime user `appuser:10001`, no build/compiler tools in runtime image.
  - Health check probe targeting `/health/live`.
  - Uvicorn server with dynamic `${PORT:-8000}`, proxy headers, and forwarded IP handling.
- **Next.js Production Dockerfile ([`apps/web/Dockerfile`](file:///Users/chandraveerrathore/projects/interview-ready/apps/web/Dockerfile))**:
  - Multi-stage image using pinned `node:22-alpine` with `output: "standalone"` NextConfig optimization.
  - Non-root runtime user `nextjs:1001`, health probe targeting `/api/health`.
- **Firebase Hosting Configuration ([`firebase.json`](file:///Users/chandraveerrathore/projects/interview-ready/firebase.json))**:
  - Conceptual rewrites routing `/api/**` to `interview-ready-api` Cloud Run service and `/**` to `interview-ready-web` Cloud Run service.
  - 1-year immutable caching for static Next.js assets (`/_next/static/**`).
- **Cloud SQL & Connection Pooling**:
  - Configurable database pooling in [`Settings`](file:///Users/chandraveerrathore/projects/interview-ready/apps/api/app/core/config.py) and [`create_database_engine`](file:///Users/chandraveerrathore/projects/interview-ready/apps/api/app/db/session.py) (`db_pool_size`, `db_max_overflow`, `db_pool_timeout`, `db_pool_recycle`, `db_pool_pre_ping`).
  - Native Cloud SQL Unix domain socket support (`/cloudsql/PROJECT:REGION:INSTANCE`).
- **Secret Manager Architecture & Cloud Run Manifests**:
  - Declarative Cloud Run manifests: [`api-service.yaml`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/cloudrun/api-service.yaml), [`web-service.yaml`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/cloudrun/web-service.yaml).
  - One-shot Alembic migration job: [`migration-job.yaml`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/cloudrun/migration-job.yaml) ensuring migrations run as a single-execution pre-deployment step.
- **Automated Deployment & Documentation**:
  - Automated deployment script: [`infrastructure/scripts/deploy.sh`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/scripts/deploy.sh).
  - Cloud SQL proxy launcher: [`infrastructure/scripts/cloud-sql-proxy.sh`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/scripts/cloud-sql-proxy.sh).
  - Detailed guides: [`docs/deployment.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/deployment.md), [`docs/environment-variables.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/environment-variables.md), [`docs/cloudsql-guide.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/cloudsql-guide.md), [`docs/migration-guide.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/migration-guide.md), [`infrastructure/README.md`](file:///Users/chandraveerrathore/projects/interview-ready/infrastructure/README.md).

### Module 13
 
 - **CI/CD Quality Gates Workflow ([`.github/workflows/ci.yml`](file:///Users/chandraveerrathore/projects/interview-ready/.github/workflows/ci.yml))**:
   - `api-quality`: Multi-service testing (PostgreSQL 16, Redis 7), Ruff lint check, Ruff format check, strict Mypy (67 source files), Alembic migrations, Pytest suite (62 tests).
   - `web-quality`: Node.js 22, ESLint, TypeScript (`tsc --noEmit`), Vitest (40 tests), Next.js 15 standalone build.
   - `desktop-quality`: TypeScript checks, Vitest (15 tests), Vite frontend build, Rust `cargo fmt --check`, `cargo clippy -- -D warnings`.
   - `security-and-secrets`: Scans for `.env` credentials, dry-run SQL migration validation (`alembic upgrade head --sql`), and npm dependency vulnerability audit.
 - **Production Deployment Pipeline ([`.github/workflows/deploy.yml`](file:///Users/chandraveerrathore/projects/interview-ready/.github/workflows/deploy.yml))**:
   - Automated quality gate verification before builds.
   - Pushes multi-stage API and Web container images to Google Artifact Registry.
   - Executes single-run database migration Cloud Run Job (`interview-ready-migrations`).
   - Updates Cloud Run API & Web services.
   - Deploys Firebase Hosting rewrites (`/api/**` to API service, `/**` to Web service).
   - Post-deployment automated HTTP smoke tests against `/health/live`, `/health/ready`, and `/api/health`.
   - Desktop release safety guard enforcing that desktop installer binaries are never published without codesigning & notarization credentials.
 - **Application & Edge Security Headers**:
   - Backend `SecurityHeadersMiddleware` ([`apps/api/app/core/middleware.py`](file:///Users/chandraveerrathore/projects/interview-ready/apps/api/app/core/middleware.py)): Enforces `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, and `Cross-Origin-Resource-Policy`.
   - Frontend `next.config.ts` ([`apps/web/next.config.ts`](file:///Users/chandraveerrathore/projects/interview-ready/apps/web/next.config.ts)): Restrictive Content-Security-Policy allowing Firebase Auth, LiveKit WebRTC, and Google Fonts, along with HSTS, X-Frame-Options, and Permissions-Policy.
   - Edge `firebase.json` ([`firebase.json`](file:///Users/chandraveerrathore/projects/interview-ready/firebase.json)): Applies edge security headers across all routes.
 - **Rate Limiting Primitives ([`apps/api/app/core/rate_limit.py`](file:///Users/chandraveerrathore/projects/interview-ready/apps/api/app/core/rate_limit.py))**:
   - Sliding window algorithm with Redis Sorted Sets (`ZSET`) and thread-safe in-memory fallback.
   - User + IP-aware identifier strategy (`u:{user_id}` or `ip:{client_ip}` with `X-Forwarded-For` parsing).
   - Standard headers on all responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
   - HTTP 429 Too Many Requests response with `Retry-After` header and standard `ApiError` envelope.
   - Protected endpoints:
     - Desktop ticket mint (`POST /auth/mint-desktop-ticket`): 10 reqs / 60s
     - Desktop ticket exchange (`POST /auth/exchange-desktop-ticket`): 15 reqs / 60s
     - Slot reservation (`POST /bookings/reserve`): 10 reqs / 60s
     - Payment checkout (`POST /payments/{booking_id}/checkout`): 10 reqs / 60s
     - Interviewer discovery & admin search (`GET /interviewers`, `GET /admin/users`, `GET /admin/audit-logs`): 60 reqs / 60s
 - **Documentation**:
   - [`docs/ci-cd.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/ci-cd.md): CI/CD pipeline reference, PR quality gates, deployment flow, and desktop release guards.
   - [`docs/security-baseline.md`](file:///Users/chandraveerrathore/projects/interview-ready/docs/security-baseline.md): Security headers table, rate limiting policies, server-side authentication guarantees, and audit practices.

## Current API surface

- `GET /health/live`
- `GET /health/ready`
- `GET /auth/me`
- `POST /auth/mint-desktop-ticket` (and `/api/v1/auth/mint-desktop-ticket`)
- `POST /auth/exchange-desktop-ticket` (and `/api/v1/auth/exchange-desktop-ticket`)
- `POST|GET|PATCH /interviewers/me/profile`
- `POST /interviewers/me/verification`
- `POST|DELETE /interviewers/me/skills[...]`
- `POST|GET|PATCH|DELETE /interviewers/me/slots[...]`
- `GET /skills`
- `GET /interviewers`
- `GET /interviewers/{interviewer_id}`
- `GET /interviewers/{interviewer_id}/slots`
- `GET /interviewers/{interviewer_id}/rating` (and `/api/v1/interviewers/{interviewer_id}/rating`)
- `GET /interviewers/{interviewer_id}/reviews` (and `/api/v1/interviewers/{interviewer_id}/reviews`)
- `POST /admin/skills`
- `PATCH /admin/interviewer-verifications/{interviewer_id}`
- `GET /admin/users` (and `/api/v1/admin/users`)
- `GET /admin/users/{user_id}` (and `/api/v1/admin/users/{user_id}`)
- `PATCH /admin/users/{user_id}/status` (and `/api/v1/admin/users/{user_id}/status`)
- `GET /admin/verifications` (and `/api/v1/admin/verifications`)
- `GET /admin/bookings` (and `/api/v1/admin/bookings`)
- `GET /admin/bookings/{booking_id}` (and `/api/v1/admin/bookings/{booking_id}`)
- `GET /admin/payments` (and `/api/v1/admin/payments`)
- `GET /admin/slots` (and `/api/v1/admin/slots`)
- `GET /admin/audit-logs` (and `/api/v1/admin/audit-logs`)
- `POST /api/v1/bookings/reserve` (and `/bookings/reserve`)
- `GET /api/v1/bookings/me` (and `/bookings/me`)
- `GET /api/v1/bookings/{booking_id}` (and `/bookings/{booking_id}`)
- `GET /api/v1/bookings/{booking_id}/join-status` (and `/bookings/{booking_id}/join-status`)
- `POST /api/v1/bookings/{booking_id}/rubric/draft` (and `/bookings/{booking_id}/rubric/draft`)
- `POST /api/v1/bookings/{booking_id}/rubric/submit` (and `/bookings/{booking_id}/rubric/submit`)
- `GET /api/v1/bookings/{booking_id}/rubric` (and `/bookings/{booking_id}/rubric`)
- `GET /api/v1/bookings/{booking_id}/feedback` (and `/bookings/{booking_id}/feedback`)
- `POST /api/v1/bookings/{booking_id}/review` (and `/bookings/{booking_id}/review`)
- `POST /api/v1/payments/{booking_id}/checkout` (and `/payments/{booking_id}/checkout`)
- `POST /api/v1/webhooks/payments/{provider}` (and `/webhooks/payments/{provider}`)
- `GET /api/v1/notifications/me` (and `/notifications/me`)
- `PATCH /api/v1/notifications/{notification_id}/read` (and `/notifications/{notification_id}/read`)
- `POST /api/v1/notifications/read-all` (and `/notifications/read-all`)
- `POST /api/v1/internal/tasks/process` (and `/internal/tasks/process`)

## Validation baseline

Last successful validation after Module 13:

```text
Backend Ruff lint: passed (0 errors)
Backend Ruff format check: passed (88 files)
Backend Strict mypy: passed (67 source files)
Backend Pytest: 62 passed (0 failures)
Alembic migration: applied through revision 20261002_0007 (SQL generation validated)
Web Vitest: 40 passed (11 test files)
Web ESLint: passed (0 errors, 0 warnings)
Web TypeScript (tsc --noEmit): passed
Next.js Production Build (next build): passed (14/14 routes generated with standalone output)
Desktop Vitest: 15 passed (3 test files)
Desktop TypeScript (tsc --noEmit): passed
Desktop Frontend Build (vite build): passed
```

Run the baseline checks with:

```bash
cd apps/api
UV_CACHE_DIR=/tmp/interview-ready-uv-cache uv run ruff check .
UV_CACHE_DIR=/tmp/interview-ready-uv-cache uv run ruff format --check .
UV_CACHE_DIR=/tmp/interview-ready-uv-cache uv run mypy app
UV_CACHE_DIR=/tmp/interview-ready-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/interview-ready-uv-cache uv run alembic upgrade head --sql

cd ../..
npm run lint:web
npm run typecheck:web
npm run test:web
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run build:web
npm run test:desktop
npm run build:desktop
```

## Known limitations and environment blockers

1. Rust/Cargo is not installed on the current machine. The desktop React frontend builds and tests cleanly, but native Tauri binary compilation has not run.
2. The Next.js 15 dependency brings an npm audit finding through its bundled PostCSS version.
3. Pytest emits a non-failing Starlette deprecation warning concerning `TestClient`/httpx integration.
4. No Git commits exist because the project directory is not a Git repository.

## Instructions for the next AI/tool

1. Read `interview-ready-codex-prompts/00_MASTER_PROJECT_CONTEXT.md` completely.
2. Read the current module prompt completely; the next one is `14_CONCURRENCY_LOAD_INTEGRATION_AND_E2E.md`.
3. Inspect this file and the existing code before making changes.
4. Implement only that module. Preserve prior behavior and do not skip ahead.
5. Keep routers thin, business rules in services, and persistence in repositories.
6. Add a new Alembic revision rather than editing applied historical revisions if DB changes are needed. The current head is `20261002_0007`.
7. Add tests for every acceptance criterion and rerun the validation baseline.
8. Update this file with the completed module, migration revision, test count, blockers, and next module.
9. Do not introduce wallet, credit-balance, or escrow behavior; the platform processes real-money slot payments.

## Module completion update template

```text
Module completed: Module 13 — CI/CD, Quality Gates, Security Baseline
Date: 2026-10-02
Summary: Comprehensive GitHub Actions PR & Deployment pipelines, edge & application security headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options, Permissions-Policy), sliding window rate limiting primitives (ticket mint/exchange, reservations, checkout, search), and desktop release guards.
Migration revision(s): 20261002_0007 (validated)
Important files:
  - .github/workflows/ci.yml
  - .github/workflows/deploy.yml
  - apps/api/app/core/rate_limit.py
  - apps/api/app/core/middleware.py
  - apps/api/app/core/errors.py
  - apps/api/app/core/auth.py
  - apps/api/app/core/config.py
  - apps/api/app/main.py
  - apps/api/app/api/auth.py
  - apps/api/app/api/bookings.py
  - apps/api/app/api/interviewers.py
  - apps/api/app/api/admin.py
  - apps/api/app/api/audit.py
  - apps/web/next.config.ts
  - firebase.json
  - apps/api/tests/test_rate_limit.py
  - apps/api/tests/test_security_headers.py
  - apps/web/src/lib/security-headers.test.ts
  - docs/ci-cd.md
  - docs/security-baseline.md
Tests added: Sliding window rate limiting tests, 429 error & header tests, API security headers test, Web security headers test
Final test count: 62 Python backend tests + 40 Web Vitest tests + 15 Desktop Vitest tests (117 total)
Commands/checks passed: Ruff lint, Ruff format check (88 files), Strict mypy (67 source files), Pytest (62 passed), Alembic SQL dry-run, Web Vitest (40 passed), Web ESLint, Web TypeScript (tsc), Next.js production build (14 routes standalone), Desktop Vitest (15 passed), Desktop TypeScript, Desktop build
Known limitations: Rust/Cargo not running locally.
Next module: Module 14 — Concurrency, Load, Integration, and End-to-End Validation
```
