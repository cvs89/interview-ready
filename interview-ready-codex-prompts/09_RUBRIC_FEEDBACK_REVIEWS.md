# Module 09 — Rubric, Feedback, Notes, Reviews

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Implement structured interviewer evaluation and candidate review safely.

## InterviewRubric

Model:
- `id UUID PK`
- `booking_id UUID FK UNIQUE NOT NULL`
- `interviewer_id UUID FK NOT NULL`
- `technical_score SMALLINT`
- `problem_solving_score SMALLINT`
- `communication_score SMALLINT`
- `detailed_feedback TEXT`
- `action_items TEXT`
- `private_interviewer_notes TEXT NULL`
- `status ENUM('DRAFT','SUBMITTED','LOCKED')`
- `created_at`
- `updated_at`
- `submitted_at NULL`
- optional `version INTEGER`

Constraints:
- scores between 1 and 5 when present
- only assigned interviewer can edit
- candidate can never access `private_interviewer_notes`

## API

Interviewer:
- save rubric draft
- submit final rubric
- complete booking after successful submission
- define whether submitted rubric is editable; default to immutable/locked unless requirements say otherwise

Candidate:
- view submitted candidate-visible feedback for own completed booking

## Review

Model:
- `id UUID PK`
- `booking_id UUID FK UNIQUE`
- `candidate_id UUID FK`
- `interviewer_id UUID FK`
- `rating SMALLINT CHECK 1..5`
- `review TEXT`
- `created_at`
- `updated_at`

Rules:
- only candidate of a COMPLETED booking can review
- one review per booking
- interviewer cannot alter candidate review
- public profile aggregate rating should be derived safely

## Booking completion

Use an explicit service transaction:
- verify actor = assigned interviewer
- verify valid booking state
- submit rubric
- transition booking to COMPLETED
- set timestamps

## Tests

- score constraints
- wrong interviewer cannot submit
- candidate cannot see private notes
- review allowed only after completion
- duplicate review rejected
- completed state transition
