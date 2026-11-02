# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phase 3 (AI provider layer) built, passing tests and confirmed against live Gemini, but not ticked: its migration isn't on `main`, so `generate()` hasn't run end to end there. Phases 1 and 2 are committed, with CI deferred.
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 3 from the roadmap line, with no detailed prompt. Design, decisions and SDK traps are in `.claude/rules/ai.md`.
- New `apps/ai`: `generate()` in `services.py` is the one gateway, `provider.py` the only file importing `google-genai`, and `AICall` both the log and the limits' counter. A Postgres advisory lock makes reserving a slot atomic. The admin is read-only.
- Added `google-genai` 2.34.0, and five settings in `.env.example`. `GEMINI_API_KEY` is required in prod. Test settings force a fake key, so a test can't spend real quota.
- Found by driving the real SDK against a fake HTTP transport: `HttpRetryOptions(attempts=0)` still retries once, so `_client()` sets `retry_config = None`. Each 429 would otherwise have cost two requests or more.
- No endpoint changed. The generated schema matches `docs/api/openapi.yaml`, so no changelog entry or inbox notice was needed.
- `uv run pytest` passed 245 of 245 on `test_neondb`, and ruff is clean. All 9 deliberate breaks of a safeguard were caught, including removing the lock. A review pass led to 2 small fixes: the longer wait wins, and the timeout now has a test.

## Verification

- Live on Gemini with the user's key, through `provider.send`: plain reply, tool request, and a tool round trip replaying `reply.steps` with their thought step. All worked on `gemini-3.5-flash-lite`. These checks used 11 requests.
- The default model changed from `gemini-3.8-flash` after its first real request hit the 25-second limit. Measurements are in `.claude/rules/ai.md`. After that one-string change, the provider tests were rerun, not the whole suite.
- Not run: `generate()` against a real call, because it needs the table. Also a real server, and `check --deploy` this session.
- `migrate` not run on `main`, so `ai_aicall` doesn't exist there yet. Nothing calls `generate()` until Phase 4, so nothing is broken.

## In progress

Nothing.

## Next steps

1. Optional: the user adds the three `AI_REQUESTS_*` limits to `.env`, just under what AI Studio shows for `gemini-3.5-flash-lite`. The defaults are guesses, because the real numbers need sign-in. `GEMINI_API_KEY` is already in `.env`.
2. With the user's approval, `uv run python manage.py migrate ai` on `main`. It's one new empty table, and `sqlmigrate` showed nothing else.
3. Check one real call: `uv run python manage.py shell -v 0 -c "from apps.ai.services import generate; print(generate('chat', 'Reply with OK.').text)"`, then see the row in the admin. Tick Phase 3 after that.
4. User commits.
5. Before Phase 4, the user decides how to handle the free tier's data terms (see `.claude/rules/ai.md`, Open): Google may use prompts, and team data would be in them.
6. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
7. For Phase 8 (deployment): hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-02.

## History

- 2026-11-01: setup session; skeleton, docs hub and agent files created.
- 2026-11-01: Phase 1 models, migrations, admin and CI built.
- 2026-11-01: Phase 2 API built, with the token blacklist applied to `main`.
- 2026-11-01: roadmap reordered, deployment + event pipeline moved to Phase 8.
- 2026-11-02: Phase 3 AI provider layer built, awaiting migration and a live check.
