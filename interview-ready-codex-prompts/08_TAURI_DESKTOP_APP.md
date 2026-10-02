# Module 08 — Tauri v2 Desktop Deep Link and Live Interview Room

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Implement secure desktop deep-link handling and LiveKit interview UI.

## Tauri configuration

Configure custom scheme:
`interviewapp://`

Use Tauri v2-supported deep-link plugin/configuration.

Apply least privilege:
- no unrestricted shell execution
- no unnecessary filesystem scope
- strict CSP
- no arbitrary remote code loading
- explicit allowlisted capabilities only

## Deep-link handling

Handle both:
- cold launch
- already-running application

Accepted route:
`interviewapp://join?ticket=...&bookingId=...`

Immediately:
1. parse input
2. validate basic format
3. exchange ticket with backend
4. clear sensitive ticket from app state as soon as possible
5. store only the returned ephemeral session state

Never log full deep-link URLs or tickets.

## Session storage

Prefer in-memory session state.
If persistence is absolutely required for reconnect, use OS-secure storage rather than plaintext files/localStorage.

## LiveKit room

Use returned:
- LiveKit URL
- room token
- room/session metadata

Implement:
- local camera/mic preview
- join/leave state
- local participant
- remote participant
- mute/unmute
- camera on/off
- connection state
- reconnect UX
- device permission error UX

## Layout

Interviewer:
- left 40%: video area
- right 60%: rubric/notes/scratchpad area

Candidate:
- video-centric layout
- shared scratchpad where enabled
- no access to interviewer-private notes

Responsive desktop layout.

## Security/error states

Handle:
- expired/replayed ticket
- invalid booking
- session expired
- LiveKit disconnect
- device permissions denied
- API unavailable

## Tests

- deep-link parser
- ticket-exchange flow
- duplicate/replayed ticket handling
- sensitive data not logged
- role-specific panel visibility
