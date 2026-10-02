# Module 10 — Notifications, Durable Jobs, Audit Trail

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Add durable background processing and operational auditability.

## Do not use FastAPI BackgroundTasks for critical workflows

Use Cloud Tasks and/or Pub/Sub abstraction for:
- reservation expiry
- booking reminders
- payment follow-up
- notification delivery
- post-interview reminders

## Notification events

Support event types such as:
- booking confirmed
- booking cancelled
- payment failed
- 24-hour reminder
- 1-hour reminder
- 10-minute join reminder
- feedback available

Implement channels behind interfaces:
- email
- optional Firebase Cloud Messaging
- in-app notifications

Do not hardcode a vendor unless configured.

## AuditLog

Model:
- `id UUID PK`
- `actor_user_id UUID NULL`
- `event_type VARCHAR NOT NULL`
- `resource_type VARCHAR`
- `resource_id VARCHAR`
- `request_id VARCHAR NULL`
- `metadata JSONB`
- `created_at TIMESTAMPTZ`

Audit:
- verification changes
- slot state changes
- booking reservation/confirmation/cancellation
- payment state changes
- refund actions
- rubric submission
- privileged admin actions

Never audit raw tokens/secrets or full payment payloads if they contain sensitive data.

## Idempotency

Durable workers must be safe to retry.

## Tests

- repeated task does not duplicate state changes
- reservation expiry is idempotent
- notification deduplication where required
- audit event is emitted for critical state changes
