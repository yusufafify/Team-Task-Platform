# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 6 are ticked, with CI deferred. Phase 7 (seed data and final coverage) is next.
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 6 from the roadmap line, with no detailed prompt: new `apps/reports`, `MonthlyReport`, `manage.py generate_reports` and `GET teams/{id}/reports/`. Design is in `.claude/rules/reports.md`.
- Python works out every number and the model writes only `body`. One request per team per month. It reads through a leader's scoped services, so no unscoped path exists.
- Leaders only, because a report rates every member. My decision, not asked: member reports would cost a request per person.
- `stats` and `members` are frozen with the prose. Quiet months spend nothing. Reruns are safe: `unique_team_month_report` plus a check before spending.
- Published: changelog, `openapi.yaml`, the "Reports" section of `overview.md`, BE-009 in both inboxes.
- With the user's approval: `migrate` and `generate_reports` ran on `main`. The Demo Team has its October report.
- Gemini use: 3 chat-model requests, all logged in `AICall`: 1 real report and 2 with made-up data, against "1, or a few more if the prompt needs tuning" as approved. The 2 made-up ones show no team.
- `brain.md` kept at 30 lines by merging two rule bullets.

## Verification

- Full suite: 574 passed. After that, 3 query-count tests, one prompt clause and a code comment were added. The report test files were rerun after the first two (47 passed), not the whole suite. Ruff, `makemigrations --check` and `spectacular --validate --fail-on-warn` are clean, and the generated schema matches `docs/api/openapi.yaml` exactly.
- 40 of 40 deliberate breaks caught, each removing one safeguard. Files restored and checked afterwards.
- The django-reviewer pass found no defects.
- On real `runserver` with real JWTs on `main`: 401 with no token, 403 for a member, 404 for a stranger, 405 on `POST`, 200 for the leader with the right shape. A rerun of the command spent no request.
- Answers read by hand: see "Checked live" in `.claude/rules/reports.md`. This found one real flaw, delays rounded to whole days, fixed in the prompt and retested.
- Never tested: a real report run with comments and chat on `main`, because October has none there. Those paths were checked by tests and by the made-up data.
- The report on `main` predates the delay wording. Its text is right as it stands, because its delay is exactly 2.0.

## Earlier work, still true

- Phases 3, 4 and 5 and the socket were checked live. Details are in `.claude/rules/ai.md`, `assistant.md`, `retrieval.md` and `api.md`.
- Never tested: `check --deploy`, a real browser or phone on the socket, Daphne on Linux, and sockets on Neon rather than SQLite, apart from the test suite.
- `main` has 5 users, the Demo Team of 4, 10 tasks, 3 comments and 3 messages, 16 `Embedding` rows and 1 `MonthlyReport`.

## In progress

Nothing.

## Next steps

1. User commits this session's changes.
2. Phase 7: seed data and final coverage. Set `SEED_USER_PASSWORD` in `.env` and rerun `seed_demo` before anyone logs in as a demo account. The seed must backdate tasks, comments and messages into the last complete month, or `generate_reports` finds a quiet month on many dates: comments and messages take the day the seed ran.
3. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
4. Mobile must confirm on a device that `Authorization` reaches the socket. The React Native JavaScript passes headers through, but its native layers weren't checked. `gunicorn` is unused now, so remove it when the host is chosen.
5. For Phase 8 (deployment): start the scheduler inside the Daphne process, as `.claude/rules/scheduling.md` decides, and add `generate_reports` to it, with a notification to leaders. The host must run one always-on Daphne process, and its `/api/*` proxy must forward WebSocket upgrades, or web runs on the polling fallback until a ticket endpoint exists. Hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api-limits.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`. Run `embed_pending` once after the first deploy.

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

- 2026-11-02: live socket for chat and notifications added.
- 2026-11-02: Phase 5 RAG built, migrated, embedded, checked live and ticked.
- 2026-11-02: Phase 6 monthly reports built, migrated, first report written, checked live and ticked.
