# Module 05 — Desktop Authentication Ticket, Session JWT, LiveKit

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Securely transfer an authenticated booking session from the browser to the Tauri desktop application.

## Redis-backed desktop ticket

Do NOT implement this as only a self-contained HMAC token because the requirement is true one-time use.

### Mint
Endpoint:

`POST /api/v1/auth/mint-desktop-ticket`

Input:
- `booking_id`

Server rules:
- Firebase-authenticated user required
- user must be either candidate or interviewer on the booking
- booking must be CONFIRMED or an explicitly permitted joinable state
- backend determines join eligibility from slot times
- default join window begins 10 minutes before start
- add a configurable grace period after scheduled end

Generate:
- at least 256 bits of cryptographically secure randomness
- return opaque ticket to caller

Redis:
- key based on `sha256(ticket)`, not raw ticket
- payload includes:
  - user_id
  - booking_id
  - role within booking
  - nonce
  - issued_at
- TTL = 60 seconds

Never log raw ticket.

### Exchange
Endpoint:

`POST /api/v1/auth/exchange-desktop-ticket`

Input:
- `ticket`
- optional booking ID only as a cross-check, never authority

Use atomic Redis `GETDEL` or equivalent Lua transaction to ensure one-time consumption.

Validate:
- ticket exists
- not expired
- booking/user binding still valid
- booking not cancelled/refunded
- join window still valid

Return:
- short-lived application session JWT
- LiveKit server URL
- LiveKit room token
- room/session metadata

## InterviewSession

Add model:
- `id UUID PK`
- `booking_id UUID FK UNIQUE`
- `livekit_room_name VARCHAR UNIQUE`
- `status ENUM('READY','ACTIVE','ENDED')`
- `candidate_joined_at NULL`
- `interviewer_joined_at NULL`
- `started_at NULL`
- `ended_at NULL`
- `created_at`

Use opaque random LiveKit room names. Do not expose predictable booking IDs as room names.

## LiveKit token permissions

Token must:
- have short TTL
- bind identity to application user/session
- allow joining only the assigned room
- use least privileges
- support publish/subscribe/data as required

## Session JWT

Use a separate signing key from unrelated application secrets.
Include:
- `sub`
- `booking_id`
- application role
- `session_id`
- `iat`
- `exp`
- `jti`

Do not make it excessively long-lived.

## API

Add join-status endpoint:

`GET /api/v1/bookings/{booking_id}/join-status`

Return:
- `can_join`
- `server_time`
- `join_available_at`
- `join_closes_at`
- machine-readable reason

## Tests

- ticket is one-time
- ticket expires
- wrong user cannot mint
- wrong booking cannot exchange
- replay fails
- cancelled booking cannot join
- backend join-window enforcement
- LiveKit token scoped to correct room
