# Module 14 — Concurrency, Load, Integration, and End-to-End Validation

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Validate the most failure-prone production paths.

## Backend concurrency tests

Use PostgreSQL, not SQLite, for lock-sensitive tests.

Scenarios:

1. Two candidates reserve one slot simultaneously.
   - exactly one 2xx
   - other gets deterministic 409
   - one PENDING_PAYMENT booking only

2. Payment webhook replay.
   - one payment transition
   - one booking confirmation
   - no duplicate side effects

3. Reservation expiry racing with payment webhook.
   - deterministic safe final state
   - paid booking must not accidentally reopen slot

4. Desktop ticket replay.
   - first exchange succeeds
   - second fails

5. Rubric double submission.
   - no duplicate completion effects

## Load tests

Add a k6 or Locust plan for:
- interviewer discovery
- availability listing
- booking reservation burst
- join-status polling
- desktop ticket mint/exchange

Measure:
- p50/p95/p99
- DB pool saturation
- error rates
- lock contention
- Redis latency
- Cloud Run concurrency assumptions

Do not invent performance targets. Put targets in configurable test documentation until product SLOs are defined.

## Web E2E

Playwright:
- candidate signup/login
- discover interviewer
- reserve slot
- simulated payment confirmation
- booking appears confirmed
- join UI respects backend join-status
- feedback visible after completion

## Desktop integration

Where automation is feasible:
- deep-link parse
- ticket exchange
- LiveKit connection mocked or test environment
- interviewer/candidate role UI

## Deliverable

Create a test report template listing:
- scenario
- expected result
- observed result
- bottleneck
- recommendation
