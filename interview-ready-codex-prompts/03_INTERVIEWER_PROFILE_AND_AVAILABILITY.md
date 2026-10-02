# Module 03 — Interviewer Profiles, Verification State, Availability Slots

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Implement interviewer profile discovery data and robust availability management.

## Models

### InterviewerVerification
- `id UUID PK`
- `interviewer_id UUID FK interviewer_profiles.id`
- `status ENUM('PENDING','IN_REVIEW','APPROVED','REJECTED')`
- `submitted_at`
- `reviewed_at`
- `reviewed_by UUID FK users.id NULL`
- `notes TEXT NULL`
- enforce one active/latest logical verification record as appropriate

### AvailabilitySlot
- `id UUID PK`
- `interviewer_id UUID FK interviewer_profiles.id NOT NULL`
- `start_time TIMESTAMPTZ NOT NULL`
- `end_time TIMESTAMPTZ NOT NULL`
- `price_minor BIGINT NOT NULL`
- `currency CHAR(3) NOT NULL`
- `status ENUM('AVAILABLE','RESERVED','BOOKED','BLOCKED') NOT NULL`
- `reserved_by UUID FK users.id NULL`
- `reservation_expires_at TIMESTAMPTZ NULL`
- `created_at`
- `updated_at`

## Constraints

- `end_time > start_time`
- `price_minor >= 0`
- index on `(interviewer_id, start_time)`
- index on `(status, start_time)`
- prevent overlapping slots for the same interviewer using a PostgreSQL exclusion constraint based on `tstzrange`, unless a carefully documented alternative is necessary
- all DB timestamps are timezone-aware UTC

## API

Interviewer:
- create/update profile
- set default pricing
- add/remove skills
- create slot
- update unbooked slot
- delete/block unbooked slot
- list own slots

Candidate:
- discover verified interviewers
- filter by:
  - skill
  - years of experience
  - price range
  - availability date/range
- fetch interviewer public profile
- fetch AVAILABLE slots only

Admin:
- review interviewer verification
- approve/reject interviewer

## Authorization

- only verified/approved interviewers can publish bookable slots
- interviewer can edit only own profile/slots
- candidates cannot access private verification notes
- public discovery never exposes sensitive user fields

## Tests

Include:
- overlapping-slot rejection
- invalid time range
- timezone-aware storage
- ownership checks
- non-verified interviewer cannot publish
- search filters
- hidden booked/reserved slot behavior

## Acceptance criteria

Availability is safe against overlap and unauthorized manipulation.
