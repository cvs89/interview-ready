# Module 11 — Admin Portal and Operational Controls

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Provide the minimum safe administrative interface required to operate the marketplace.

## Admin capabilities

- list/search users
- view interviewer verification queue
- approve/reject interviewer
- inspect interviewer profiles
- inspect bookings
- inspect payment status
- inspect slot state
- inspect non-sensitive audit trail
- disable/block abusive accounts if account status model exists
- trigger safe support actions only where explicitly implemented

## Safety rules

Admin endpoints require ADMIN role.
All admin mutations must create audit records.
Never expose:
- Firebase tokens
- LiveKit secrets/tokens
- raw desktop tickets
- payment secret keys
- private credentials

## Optional account state

If needed, add:
- ACTIVE
- SUSPENDED
- DISABLED

Do not invent automatic suspension rules.

## UI

Build basic operational pages in Next.js with:
- table pagination
- filtering
- clear status indicators
- confirmation dialogs for destructive actions
- error handling
- audit context

## Tests

- non-admin denied
- admin actions audited
- verification transitions validated
- sensitive fields absent from responses
