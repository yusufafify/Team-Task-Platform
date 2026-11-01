# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-01
- Roadmap phase: setup complete, waiting for skills + phase 1
- Repository: `yusufafify/Team-Task-Platform`, branch `main`. Only the user commits.

## Done last session

- Installed uv and created the project on the existing Python 3.11.9 `.venv` (D-009).
- Added the foundation dependencies, the `config` project, the settings split, pytest, ruff, `.env.example`, `.gitignore` and `README.md`.
- Bootstrapped the root `CLAUDE.md` and the `/docs` hub.
- Created the backend agent files and commands.
- Applied the permission rules and tested them: writes to `/web` and `/mobile` are refused, `.env` is denied, `.env.example` stays readable and editable.
- Ran /sync-skills: all skills and conflicts are in `.claude/skills-index.md`. Excluded `.claude` from ruff.
- Compacted `CLAUDE.md`; `/sync-skills` now writes to `.claude/skills-index.md`.
- Installed `gemini-api-dev` as a real folder in `.claude/skills/`, from `google-gemini/gemini-skills` at `39d81f4`.
- Replaced the dead `resend` and `email-best-practices` links with real folders in `.claude/skills/`, from `resend/resend-skills` at `b2ae7b1`. Hashes match `skills-lock.json`.
- Made `DJANGO_SETTINGS_MODULE` in `.env` the only way to choose dev or prod; entry-point defaults removed, covered by `tests/test_environment.py`.
- Added host deployment steps to `README.md`. Working locally until a host is chosen; the suggested free setup is Render's web service with Neon Postgres.
- User created a Neon database in eu-central-1. Tested it: connection, TLS, pgvector 0.8.6 and an HNSW query all work, with the pgvector test rolled back. `neondb` is still empty. pgvector is not enabled yet; Phase 6 enables it through a migration with `VectorExtension`.

- Reviewed the setup against best practices at the user's request. Tests now use a temporary `test_neondb` on the Neon test branch, `main` and `test` have separate jobs, `CorsMiddleware` comes first, prod logs to the console, the HSTS default is 3600, and the roadmap is updated. No migration has run on any branch yet.
- Set up graphify for `/backend` only. No commit hook yet, because there's no git repository.
- Audited the setup against solid, clean-code, anti-over-engineer, software-backend and software-search. Fixed four findings: pytest settings pin, prod connection reuse, prod log format, and the `DATABASE_URL` guard refusing a local CI database.
- User removed `-pooler` from both URLs. `uv run pytest` passed 18 of 18, including the database test.
- At the user's request, copied the Elyria project's Neon split: pooled `DATABASE_URL` for the app, `DIRECT_URL` for `migrate`, direct `TEST_DATABASE_URL` for tests.
- Audit items still open, none started: `/healthz` and `/readyz`, correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## In progress

Nothing. Changes wait in the working tree for the user to commit.

## Next steps

1. Wait for the Phase 1 prompt.

## Blockers / waiting on other agents

- User: allow reads of `docs/`. `.claude/settings.json` already lists it, but `permissions.blockReadsOutsideWorkingDirectories` refused the reads, so session-start is incomplete and the inbox and status are unread.
- User: in `.env`, put `-pooler` back in `DATABASE_URL`, add `connect_timeout=5`, and add `DIRECT_URL` with the direct host. Until then everything still works, on the direct URL.
- `main` serves local work and prod, by the user's decision, so confirm before any `migrate` or data change. Agents can't read or edit `.env`.

## Inbox processed up to

None

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
