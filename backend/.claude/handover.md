# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 7 are ticked, with CI deferred. Phase 8 (deployment and event pipeline) is next.
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 7 from the roadmap line, with no detailed prompt.
- `seed_demo` now fills the last complete month as well as the days around today: 6 more tasks, 4 more comments and 4 more messages. Task, comment and message dates are backdated, so `generate_reports` finds a real month on any date. Design is in `.claude/rules/assistant.md`.
- "Audit last quarter's expenses" moved into the month rows, because its old 35-day offset only landed there on some dates. It also had a completion date before its creation date, which the backdating fixes.
- New tests: one walks every team and task route with every method as another team's leader, including `PUT`, which no test tried. Others check that `openapi.yaml` matches the code, a forged host gets the JSON 400, and a refused socket disconnects cleanly.
- No endpoint, payload or error format changed, so there's no changelog entry or inbox notice.
- Coverage is measured with `uv run --with pytest-cov`, so nothing was added to the lockfile. The command is in `.claude/rules/testing.md`.
- My decisions, not asked: no second team, no seeded notifications, no `pytest-cov` dependency or coverage gate in CI.
- With the user's approval, on `main`: reran `seed_demo`, deleted the Demo Team's October report, and ran `generate_reports`. That spent 1 Gemini request, as approved. The old report's text is in the session scratchpad only.

## Verification

- Full suite on the final code: 592 passed. Ruff, `ruff format --check` and `makemigrations --check` are clean. The schema test confirms `docs/api/openapi.yaml` matches.
- Coverage went from 98% to 99%. What's left is `__str__` methods, `wsgi.py`, which nothing runs, and `prod.py` and the guards in `test.py`, which `tests/test_environment.py` covers in a subprocess coverage can't see.
- 12 of 12 deliberate breaks caught, each removing one safeguard. Files restored and checked afterwards.
- Seed dates are tested on 5 awkward dates, including just after February and across a year.
- October's new report was read by hand against `main`: every number, per-person rate and claim was right, and nothing was invented.
- That report's flaw: it was sent 6 comments and 5 messages and used none, so blocked work has no cause beside it. Prompt left alone: see "Open" in `.claude/rules/reports.md`.
- 13 of the 29 tasks, comments and messages on `main` have no `Embedding` row yet. They embed on the next search, in one request.

## Phase 6 results, still true

- Python works out every report number and the model writes only `body`. Design is in `.claude/rules/reports.md`.
- 577 tests and 40 deliberate breaks at commit `55a8836`, plus a real `runserver` check with real JWTs on `main`.

## Earlier work, still true

- Phases 3, 4 and 5 and the socket were checked live. Details are in `.claude/rules/ai.md`, `assistant.md`, `retrieval.md` and `api.md`.
- Never tested: `check --deploy`, a real browser or phone on the socket, Daphne on Linux, and sockets on Neon rather than SQLite, apart from the test suite.
- `main` has 5 users, the Demo Team of 4, 15 tasks, 7 comments and 7 messages, 16 `Embedding` rows and 1 `MonthlyReport`.

## In progress

Nothing.

## Next steps

1. The four demo accounts still can't log in: the seed saw no `SEED_USER_PASSWORD`, confirmed by `has_usable_password()` on `main`. The user sets it in `.env`, then `seed_demo` reruns. That spends nothing and leaves the report alone.
2. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
3. Mobile must confirm on a device that `Authorization` reaches the socket. The React Native JavaScript passes headers through, but its native layers weren't checked. `gunicorn` is unused now, so remove it when the host is chosen.
4. For Phase 8 (deployment): start the scheduler inside the Daphne process, as `.claude/rules/scheduling.md` decides, and add `generate_reports` to it, with a notification to leaders. The host must run one always-on Daphne process, and its `/api/*` proxy must forward WebSocket upgrades, or web runs on the polling fallback until a ticket endpoint exists. Hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api-limits.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`. Run `embed_pending` once after the first deploy.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.
- `.claude/rules/architecture.md` is 57 lines, over the 50-line cap. `brain.md` is at its cap of 30, so splitting it means freeing a line there first.

## Inbox processed up to

None: the inbox was empty on 2026-11-02.

## History

- 2026-11-02: Phase 5 RAG built, migrated, embedded, checked live and ticked.
- 2026-11-02: Phase 6 monthly reports built, migrated, first report written, checked live and ticked.
- 2026-11-02: Phase 7 seed and final coverage built, applied to `main`, report rewritten, checked by hand and ticked.
