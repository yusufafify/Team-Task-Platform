# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-01
- Roadmap phase: Phase 1 built, applied to `main` and pushed; only the first CI run is left
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built `accounts`, `teams`, `tasks`, `chat` and `notifications`: models, initial migrations and admin.
- With the user's approval, applied all 23 migrations to Neon `main` through the direct host and ran `createcachetable`. Verified: none left unapplied, and the tables and constraints exist.
- No detailed Phase 1 prompt existed, so the schema came from the roadmap line and the glossary. Choices and deletion tiers are in `.claude/rules/domain-model.md`.
- Added tests for constraints, the deletion policy, admin pages, email login and model/migration drift, plus `tests/factories.py`. `uv run pytest --create-db` passed 64 of 64 on `test_neondb`. The rebuild was needed because the old test database was migrated with `auth.User`.
- `tests/test_environment.py` now copies `apps` as well as `config`.
- Added `.github/workflows/backend.yml`. actionlint passes, but the workflow has never run.
- User pushed commit `59195a3`, created a superuser and logged in to the admin on `main`. A 403 on `localhost` came from a stale browser `csrftoken` cookie, not from the code.
- No API change, so no changelog entry, `openapi.yaml` or inbox notice.
- At the user's request, moved scheduled jobs off GitHub Actions: D-015 supersedes D-002's trigger, and `.claude/rules/scheduling.md` holds the design and its limits. Plan only; nothing is built. The root `README.md` and `TODO.md` may still mention the old cron, and weren't checked.

## In progress

Nothing.

## Next steps

1. Once the billing lock is cleared and the Backend workflow passes, tick Phase 1 in `.claude/roadmap.md` and `docs/status.md`.
2. Wait for the Phase 2 prompt. Its task service must keep `completed_at` in step with the status, and must check that assignees belong to the team.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". Only the user can clear it, then re-run the job. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- Root `README.md` and `TODO.md` are outside the read scope, so the schema wasn't checked against them. Needs `/add-dir D:\work\Nesma-Airlines` to read them.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: `/healthz` and `/readyz`, correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-01.

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
- 2026-11-01: Phase 1 models, migrations, admin and CI built.
