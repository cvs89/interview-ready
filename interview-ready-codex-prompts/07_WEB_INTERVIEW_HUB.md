# Module 07 — Web Booking Dashboard and Join Call Experience

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Build the candidate/interviewer booking hub and secure hand-off to desktop.

## Booking dashboard

Candidate:
- upcoming interviews
- completed interviews
- cancelled/expired interviews
- payment state

Interviewer:
- upcoming interviews
- completed interviews
- candidate-safe information only

## Join Call card

For each confirmed upcoming booking:
- fetch backend join-status
- display scheduled local time
- display countdown
- enable Join only when backend reports `can_join=true`

On Join:
1. call `/api/v1/auth/mint-desktop-ticket`
2. receive one-time ticket
3. launch:
   `interviewapp://join?ticket=<encoded_ticket>&bookingId=<booking_id>`
4. never print/log the deep link
5. show fallback UI if desktop app is not detected within a short interval

Fallback modal:
- Windows download link
- macOS download link
- Linux download link
- retry-open button
- installation/deep-link guidance

Links must come from environment/configuration, not hard-coded fake URLs.

## Browser detection

Implement best-effort fallback behavior without claiming certainty that the app is installed.

## Security

- do not persist desktop ticket
- do not include ticket in analytics
- avoid rendering ticket into reusable DOM history where possible
- mint a fresh ticket for each retry

## Tests

- join disabled outside window
- join-status drives UI
- deep-link properly URL-encodes ticket
- fallback appears
- repeated retry obtains a new ticket
