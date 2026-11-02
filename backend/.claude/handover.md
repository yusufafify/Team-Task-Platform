# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 3 are ticked, with CI deferred. Phase 4 is next, and needs one decision from the user first (see Next steps).
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 3 from the roadmap line, with no detailed prompt. Design, decisions and SDK traps are in `.claude/rules/ai.md`.
- New `apps/ai`: `generate()` in `services.py` is the one gateway, `provider.py` the only file importing `google-genai`, and `AICall` both the log and the limits' counter. A Postgres advisory lock makes reserving a slot atomic. The admin is read-only.
- Added `google-genai` 2.34.0, and five settings in `.env.example`. `GEMINI_API_KEY` is required in prod. Test settings force a fake key, so a test can't spend real quota.
- Found by driving the real SDK against a fake HTTP transport: `HttpRetryOptions(attempts=0)` still retries once, so `_client()` sets `retry_config = None`. Each 429 would otherwise have cost two requests or more.
- No endpoint changed. The generated schema matches `docs/api/openapi.yaml`, so no changelog entry or inbox notice was needed.
- All 9 deliberate breaks of a safeguard were caught, including removing the lock. A review pass led to 2 small fixes: the longer wait wins, and the timeout now has a test.
- Finished Phase 3: migrated `main`, made one real call, reran the full suite and ticked the roadmap.
- Added the user's graphify rule to `CLAUDE.md` and memory. Tested details are in `.claude/rules/agent-setup.md`. The first `graphify update` took the graph from 105 to 634 nodes and dropped 43 concepts extracted from docs. The old graph is in `graphify-out/curated-2026-11-01/`.

## Verification

- Live on Gemini with the user's key, through `provider.send`: plain reply, tool request, and a tool round trip replaying `reply.steps` with their thought step. All worked on `gemini-3.5-flash-lite`. These checks used 11 requests.
- The default model changed from `gemini-3.8-flash` after its first real request hit the 25-second limit. Measurements are in `.claude/rules/ai.md`.
- `migrate ai` ran on `main` with the user's approval. `migrate ai --plan` showed only `Create model AICall`.
- One real `generate()` call on `main` replied `OK.` and logged row 1 as `succeeded`, at 7 tokens and 1375 ms. The row was read from the database, not from the admin page.
- After that, `uv run pytest` passed 245 of 245 on `test_neondb`, and `uv run ruff check` was clean.
- Not run: a real server, and `check --deploy` this session.

## In progress

Nothing.

## Next steps

1. Optional: the user adds the three `AI_REQUESTS_*` limits to `.env`, just under what AI Studio shows for `gemini-3.5-flash-lite`. The defaults are guesses, because the real numbers need sign-in. `GEMINI_API_KEY` is already in `.env`.
2. User commits this session's changes.
3. Before Phase 4, the user decides how to handle the free tier's data terms (see `.claude/rules/ai.md`, Open): Google may use prompts, and team data would be in them.
4. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
5. For Phase 8 (deployment): hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: correlation IDs, rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.

## Inbox processed up to

None: the inbox was empty on 2026-11-02.

## History

- 2026-11-01: roadmap reordered, deployment + event pipeline moved to Phase 8.
- 2026-11-02: Phase 3 AI provider layer built.
- 2026-11-02: Phase 3 migrated, checked with a real call and ticked; graphify rule added.
