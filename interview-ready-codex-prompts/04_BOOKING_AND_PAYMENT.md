# Module 04 — Slot Reservation, Booking, Payment, Webhook Confirmation

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Implement race-safe paid slot booking with temporary reservation and trusted webhook confirmation.

There is NO credit wallet and NO escrow.

## Models

### Booking
- `id UUID PK`
- `slot_id UUID FK availability_slots.id UNIQUE NOT NULL`
- `candidate_id UUID FK users.id NOT NULL`
- `interviewer_id UUID FK users.id NOT NULL` or FK interviewer profile as consistently designed
- `status ENUM(
    'PENDING_PAYMENT',
    'CONFIRMED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    'EXPIRED',
    'NO_SHOW',
    'REFUNDED'
  )`
- `price_minor BIGINT NOT NULL`
- `currency CHAR(3) NOT NULL`
- `created_at`
- `confirmed_at NULL`
- `started_at NULL`
- `completed_at NULL`
- `cancelled_at NULL`

The price/currency are a snapshot copied from the slot when reserved.

### Payment
- `id UUID PK`
- `booking_id UUID FK bookings.id UNIQUE NOT NULL`
- `candidate_id UUID FK users.id NOT NULL`
- `provider VARCHAR NOT NULL`
- `provider_payment_id VARCHAR UNIQUE NULL`
- `provider_checkout_session_id VARCHAR UNIQUE NULL`
- `amount_minor BIGINT NOT NULL`
- `currency CHAR(3) NOT NULL`
- `status ENUM('PENDING','REQUIRES_ACTION','PAID','FAILED','REFUNDED','PARTIALLY_REFUNDED','CANCELLED')`
- `created_at`
- `updated_at`
- `paid_at NULL`
- `refunded_at NULL`

### PaymentWebhookEvent
- `id UUID PK`
- `provider VARCHAR`
- `provider_event_id VARCHAR UNIQUE`
- `event_type VARCHAR`
- `payload JSONB`
- `processed_at NULL`
- `created_at`

## Reservation endpoint

Implement:

`POST /api/v1/bookings/reserve`

Request contains only a `slot_id`.

Algorithm must be transaction-safe:

1. Begin DB transaction.
2. `SELECT AvailabilitySlot ... FOR UPDATE`.
3. If expired reservation exists, normalize it back to AVAILABLE before evaluating.
4. Require status AVAILABLE.
5. Require start_time in the future.
6. Set:
   - status = RESERVED
   - reserved_by = current candidate
   - reservation_expires_at = now + configurable 10 minutes
7. Create Booking with `PENDING_PAYMENT`.
8. Snapshot `price_minor` and `currency`.
9. Commit.
10. Return booking and reservation-expiry information.

Concurrent reservation attempts for the same slot must result in exactly one success.

## Payment checkout

Implement an abstract payment provider interface:
- `create_checkout(...)`
- `verify_webhook(...)`
- `refund(...)`

Provide one concrete provider only if explicitly configured in the repository; otherwise add a clean test/dev provider and clear integration seam.

Endpoint:

`POST /api/v1/payments/{booking_id}/checkout`

Rules:
- caller must own the booking
- booking must be PENDING_PAYMENT
- reservation must not be expired
- checkout amount must always come from Booking, never from client payload

## Webhook

`POST /api/v1/webhooks/payments/{provider}`

On verified success event, inside a DB transaction:
- deduplicate using `provider_event_id`
- lock booking and slot rows
- verify amounts/currency against Booking
- mark Payment PAID
- mark Booking CONFIRMED
- mark Slot BOOKED
- clear reservation fields

Never trust browser redirect as payment confirmation.

## Reservation expiry

Implement a durable job/task or periodic worker operation:
- find expired RESERVED slots / PENDING_PAYMENT bookings
- lock rows
- if no successful payment:
  - booking -> EXPIRED
  - slot -> AVAILABLE
  - clear reservation fields

Make operation idempotent.

## Cancellation/refund foundation

Add service-layer hooks/state transitions without inventing a business refund policy.
Use configuration/placeholders for policy decisions until product rules are supplied.

## Tests

Required concurrency/integration tests:
- two users reserve same slot simultaneously -> one succeeds, one 409
- booking stores price snapshot
- expired reservation becomes available
- forged client price is ignored
- webhook replay is harmless
- invalid webhook signature fails
- payment success confirms booking and books slot
- failed payment does not book slot
- unauthorized user cannot pay another booking

Use real PostgreSQL integration tests if possible because row locking behavior must be validated on PostgreSQL.
