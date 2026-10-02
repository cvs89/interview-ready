# Module 06 — Next.js Web Authentication and Interviewer Marketplace

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Build the authenticated web portal foundation and interviewer discovery experience.

## Firebase Auth

Create `AuthContext.tsx` supporting:
- Google sign-in
- email/password sign-up
- email/password sign-in
- logout
- auth loading state
- Firebase user access
- token retrieval

Do not store ID tokens in localStorage manually.

## API client

Create a reusable client for `/api/v1/*` that:
- gets fresh Firebase ID token as needed
- sends `Authorization: Bearer <token>`
- handles 401/403 consistently
- parses the standard API error envelope
- supports request cancellation where useful

## Routes/pages

Create:
- sign in
- sign up
- candidate dashboard
- interviewer discovery
- interviewer profile/details
- slot selection

## Interviewer discovery

Filters:
- skills
- experience
- price
- availability

Include:
- loading state
- empty state
- pagination/cursor support
- accessible filter controls
- mobile responsiveness

## Slot selection

Display:
- local-time conversion from UTC
- duration
- price formatted using currency
- timezone indicator
- slot state

Do not infer availability only from cached UI state. Handle 409 conflict from reservation endpoint cleanly.

## Booking flow

When candidate clicks a slot:
- call reservation endpoint
- show reservation countdown based on server `reservation_expires_at`
- continue to checkout
- do not mark payment successful from client-side redirect alone
- success page should poll/refetch booking state until webhook confirmation or timeout

## Tests

- auth context
- authenticated API client
- filter UI
- slot conflict handling
- reservation countdown
- payment redirect does not falsely confirm booking
