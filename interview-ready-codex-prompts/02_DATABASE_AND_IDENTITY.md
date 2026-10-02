# Module 02 — Database Schema, Alembic, Firebase Authentication, RBAC

Read `00_MASTER_PROJECT_CONTEXT.md` first.

## Goal

Implement the foundational domain schema and Firebase-backed identity layer.

## Database models

### User
- `id UUID PK`
- `firebase_uid VARCHAR UNIQUE NOT NULL`
- `email CITEXT or normalized VARCHAR UNIQUE NOT NULL`
- `full_name VARCHAR NOT NULL`
- `role ENUM('CANDIDATE','INTERVIEWER','ADMIN') NOT NULL`
- `email_verified BOOLEAN NOT NULL DEFAULT FALSE`
- `auth_provider VARCHAR NULL`
- `last_login_at TIMESTAMPTZ NULL`
- `created_at TIMESTAMPTZ NOT NULL`
- `updated_at TIMESTAMPTZ NOT NULL`

### InterviewerProfile
- `id UUID PK`
- `user_id UUID FK users.id UNIQUE NOT NULL`
- `bio TEXT`
- `title VARCHAR`
- `years_experience INTEGER`
- `default_rate_minor BIGINT`
- `currency CHAR(3)`
- `is_verified BOOLEAN NOT NULL DEFAULT FALSE`
- `created_at`
- `updated_at`

### Skill
- `id UUID PK`
- `name VARCHAR UNIQUE NOT NULL`
- `slug VARCHAR UNIQUE NOT NULL`

### InterviewerSkill
- `interviewer_id FK`
- `skill_id FK`
- optional `years_experience`
- composite unique constraint

Do not use an unindexed free-form JSON array as the primary skill-search model.

## Authentication middleware/dependencies

Implement Firebase token validation from:

`Authorization: Bearer <Firebase ID token>`

Use `firebase_admin.auth.verify_id_token`.

On successful authentication:
- derive Firebase UID/email from the verified token only
- fetch or auto-register user
- update safe login metadata
- never accept client-provided role as authoritative

Provide:
- `get_current_user`
- `require_role(...)`
- reusable ownership/authorization helpers

Default newly auto-created users to `CANDIDATE` unless an explicit approved onboarding route assigns interviewer status.

## Alembic

Create:
- `env.py`
- initial migration
- PostgreSQL enums/extensions as required
- constraints/indexes

## Tests

Cover:
- missing token
- malformed token
- invalid token
- valid token
- first-login user creation
- repeated login does not duplicate user
- role enforcement
- disabled/unverified access rules where applicable

Mock Firebase verification cleanly in unit tests.

## Acceptance criteria

- Firebase UID is not the database primary key.
- No user can elevate their role by modifying request payloads.
- Schema is fully migrated through Alembic.
- Tests pass.
