# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-01
- Roadmap phase: Phase 2 built and passing locally, not committed; Phases 1 and 2 both wait on the first CI run
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 2 with no detailed prompt, from the roadmap line and glossary. Patterns, product decisions and limits are in `.claude/rules/api.md`.
- Endpoints under `/api/v1/`: auth, teams and members, tasks, comments, chat, notifications, device tokens, stats. Also JSON errors, pagination, login and register throttles, `/healthz` and `/readyz`.
- Our apps have no schema change. `DeviceToken`'s validator moved to a module constant, and `makemigrations --check` confirms no drift.
- The user then asked to fix the listed risks before committing. Done: refresh rotation, token blacklist, `auth/logout/` and `auth/logout-all/`; required `DJANGO_NUM_PROXIES`; a login lockout fix; stricter client polling rules, sent as BE-002.
- With the user's approval, applied the 12 `token_blacklist` migrations to `main`: 35 applied, none pending, both new tables empty. The SQL touched only those two tables.
- `uv run pytest` passed 191 of 191 on `test_neondb`. ruff is clean, `spectacular --validate --fail-on-warn` is clean, and `check --deploy` passes with throwaway prod values.
- A `django-reviewer` pass found 4 bugs and 1 awkward default, each confirmed by a failing test and fixed. Lessons are in `.claude/rules/api.md`.
- Published `docs/api/openapi.yaml`, `overview.md` and the changelog entry, and sent BE-001 to the web and mobile inboxes.
- Not run: a real server, any client, or concurrent requests. The leader lock and throttles were tested only one request at a time.

## In progress

Nothing.

## Next steps

1. Fix the root `README.md` and `TODO.md`, which the user asked for. It's blocked until they run `/add-dir D:\work\Nesma-Airlines`. Replace the cron references using D-015, and update the state table. The user wants this before committing.
2. User reviews and commits Phase 2.
3. Once the billing lock is cleared and the Backend workflow passes, tick Phases 1 and 2 in `.claude/roadmap.md` and `docs/status.md`.
4. Wait for the Phase 3 prompt. When it picks a host, set `DJANGO_NUM_PROXIES`, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". Only the user can clear it, then re-run the job. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- Root `README.md` and `TODO.md` are outside the read scope. They still describe the old cron trigger and the skeleton state, and can be edited only when the user asks. Reading them needs `/add-dir D:\work\Nesma-Airlines`; don't go around it with Bash.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-01.

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
- 2026-11-01: Phase 1 models, migrations, admin and CI built.
- 2026-11-01: Phase 2 API built, with the token blacklist applied to `main`.
