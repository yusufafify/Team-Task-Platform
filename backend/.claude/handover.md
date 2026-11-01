# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-01
- Roadmap phase: Phases 1 and 2 ticked at the user's request, with CI deferred. Phase 2 isn't committed yet
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 2 with no detailed prompt, from the roadmap line and glossary. Patterns, product decisions and limits are in `.claude/rules/api.md`.
- Endpoints under `/api/v1/`: auth, teams and members, tasks, comments, chat, notifications, device tokens, stats. Also JSON errors, pagination, login and register throttles, `/healthz` and `/readyz`.
- Our apps have no schema change. `DeviceToken`'s validator moved to a module constant, and `makemigrations --check` confirms no drift.
- The user then asked to fix the listed risks before committing. Done: refresh rotation, token blacklist, `auth/logout/` and `auth/logout-all/`; required `DJANGO_NUM_PROXIES`; a login lockout fix; stricter client polling rules, sent as BE-002.
- With the user's approval, applied the 12 `token_blacklist` migrations to `main`: 35 applied, none pending, both new tables empty. The SQL touched only those two tables.
- The user then chose `HttpOnly` cookies for both web tokens, and the encrypted keychain for mobile through separate `auth/mobile/*` endpoints. Built and sent as BE-003, with no further migration.
- `uv run pytest` passed 211 of 211 on `test_neondb`. ruff is clean, `spectacular --validate --fail-on-warn` is clean, and `check --deploy` passes with throwaway prod values.
- A `django-reviewer` pass found 4 bugs and 1 awkward default, each confirmed by a failing test and fixed. Lessons are in `.claude/rules/api.md`.
- Published `docs/api/openapi.yaml`, `overview.md` and the changelog entry, and sent BE-001 to the web and mobile inboxes.
- Not run: a real server, any client, or concurrent requests. The leader lock and throttles were tested only one request at a time.

## In progress

Nothing.

## Next steps

1. User reviews and commits Phase 2.
2. When the user clears the billing lock, run the Backend workflow, because Phases 1 and 2 were ticked without it.
3. Wait for the Phase 3 prompt. Hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-01.

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
- 2026-11-01: Phase 1 models, migrations, admin and CI built.
- 2026-11-01: Phase 2 API built, with the token blacklist applied to `main`.
