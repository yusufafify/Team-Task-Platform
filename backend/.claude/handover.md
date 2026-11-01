# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-01
- Roadmap phase: Phase 1 built and applied to `main`; the first CI run is pending
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built `accounts`, `teams`, `tasks`, `chat` and `notifications`: models, initial migrations and admin.
- With the user's approval, applied all 23 migrations to Neon `main` through the direct host and ran `createcachetable`. Verified: none left unapplied, and the tables and constraints exist.
- No detailed Phase 1 prompt existed, so the schema came from the roadmap line and the glossary. Choices and deletion tiers are in `.claude/rules/domain-model.md`.
- Added tests for constraints, the deletion policy, admin pages, email login and model/migration drift, plus `tests/factories.py`. `uv run pytest --create-db` passed 64 of 64 on `test_neondb`. The rebuild was needed because the old test database was migrated with `auth.User`.
- `tests/test_environment.py` now copies `apps` as well as `config`.
- Added `.github/workflows/backend.yml`. actionlint passes, but the workflow has never run.
- No API change, so no changelog entry, `openapi.yaml` or inbox notice.

## In progress

Nothing. Changes wait in the working tree for the user to commit.

## Next steps

1. After the first push, check that the Backend workflow passes, then tick Phase 1 in `.claude/roadmap.md` and `docs/status.md`.
2. Wait for the Phase 2 prompt. Its task service must keep `completed_at` in step with the status, and must check that assignees belong to the team.

## Blockers / waiting on other agents

- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- User: `uv run python manage.py createsuperuser` is interactive, so the user runs it.
- Root `README.md` and `TODO.md` are outside the read scope, so the schema wasn't checked against them. Needs `/add-dir D:\work\Nesma-Airlines` to read them.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: `/healthz` and `/readyz`, correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-01.

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
- 2026-11-01: Phase 1 models, migrations, admin and CI built.
