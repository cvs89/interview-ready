# How to Use These Codex Prompt Files

Use the prompts sequentially.

Recommended order:

1. `00_MASTER_PROJECT_CONTEXT.md`
2. `01_REPOSITORY_FOUNDATION.md`
3. `02_DATABASE_AND_IDENTITY.md`
4. `03_INTERVIEWER_PROFILE_AND_AVAILABILITY.md`
5. `04_BOOKING_AND_PAYMENT.md`
6. `05_DESKTOP_TICKET_AND_LIVEKIT.md`
7. `06_WEB_AUTH_AND_MARKETPLACE.md`
8. `07_WEB_INTERVIEW_HUB.md`
9. `08_TAURI_DESKTOP_APP.md`
10. `09_RUBRIC_FEEDBACK_REVIEWS.md`
11. `10_NOTIFICATIONS_JOBS_AND_AUDIT.md`
12. `11_ADMIN_AND_OPERATIONS.md`
13. `12_INFRASTRUCTURE_AND_DEPLOYMENT.md`
14. `13_CI_CD_QUALITY_AND_SECURITY.md`
15. `14_LOAD_CONCURRENCY_AND_E2E_TESTING.md`
16. `15_FINAL_PRODUCTION_READINESS_REVIEW.md`

## Recommended way to prompt Codex

For every new stage, provide Codex:

> Read `00_MASTER_PROJECT_CONTEXT.md` and `<CURRENT_MODULE>.md`. Inspect the existing repository before making changes. Implement only this module. Preserve prior working behavior. Add tests and run the relevant checks. Stop when this module is complete and report files changed, migrations, tests, commands run, and any blockers.

## Important

Do not ask Codex to generate the entire platform in one prompt.

Each module should finish with passing tests before starting the next one.

Commit after each module, for example:

```bash
git add .
git commit -m "feat: complete module 04 booking and payments"
```

This makes rollback and review much safer.
