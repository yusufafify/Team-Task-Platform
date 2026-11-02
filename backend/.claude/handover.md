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
- At the user's request, checked auth and errors against software-backend, clean code and SOLID before Phase 4. Added `config/exceptions.py` (stable `code`, Django `ValidationError` as 400, which fixed a crafted-cursor 500), `config/request_id.py`, and a test that walks every URL. Decisions are in `.claude/rules/api.md`. Published as BE-005, with a changelog entry. `openapi.yaml` regenerated with no diff.
- Split `.claude/rules/api-limits.md` out of `api.md`, which was over the 50-line cap.

## Verification

- Live on Gemini with the user's key, through `provider.send`: plain reply, tool request, and a tool round trip replaying `reply.steps` with their thought step. All worked on `gemini-3.5-flash-lite`. These checks used 11 requests.
- The default model changed from `gemini-3.8-flash` after its first real request hit the 25-second limit. Measurements are in `.claude/rules/ai.md`.
- `migrate ai` ran on `main` with the user's approval. `migrate ai --plan` showed only `Create model AICall`.
- One real `generate()` call on `main` replied `OK.` and logged row 1 as `succeeded`, at 7 tokens and 1375 ms. The row was read from the database, not from the admin page.
- After the error and request ID work, the full suite ran 315 passed and 1 failed. The failure was the middleware-order test, which pinned the old order. Only that test's assertion changed afterwards, and it was rerun alone, not the whole suite. No production code changed after the full run.
- 11 of 11 deliberate breaks were caught, including a private view losing `IsAuthenticated` and an unlisted public route. One was missed at first, which added the `user_inactive` test.
- A throwaway probe sent 240 requests to the 16 protected routes with no token and bad tokens, all 401, and 146 malformed requests, with no 500 and no body outside the documented shapes.
- Not run: a real server, and `check --deploy` this session.

## In progress

Nothing.

## Next steps

1. Optional: the user adds the three `AI_REQUESTS_*` limits to `.env`, just under what AI Studio shows for `gemini-3.5-flash-lite`. The defaults are guesses, because the real numbers need sign-in. `GEMINI_API_KEY` is already in `.env`.
2. User commits this session's changes.
3. Before Phase 4, the user decides how to handle the free tier's data terms (see `.claude/rules/ai.md`, Open): Google may use prompts, and team data would be in them.
4. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
5. For Phase 8 (deployment): hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api-limits.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: rollback and smoke steps, dependency scan in CI, and removing boilerplate docstrings.
- `.claude/rules/architecture.md` is 56 lines, over the 50-line cap. Splitting it needs a new row, and `brain.md` has room for only one more line before its own cap.

## Inbox processed up to

None: the inbox was empty on 2026-11-02.

## History

- 2026-11-02: Phase 3 AI provider layer built.
- 2026-11-02: Phase 3 migrated, checked with a real call and ticked; graphify rule added.
- 2026-11-02: error codes, request IDs and a route guard test added before Phase 4.
