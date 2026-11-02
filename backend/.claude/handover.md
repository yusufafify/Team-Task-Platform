# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 4 are ticked, with CI deferred. Phase 5 (RAG) is next.
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
- Built Phase 4 from the roadmap line: `apps/assistant` with snapshot, four read-only tools, tool loop and answer cache. Design is in `.claude/rules/assistant.md`. Published as BE-006, with a changelog entry, overview section and regenerated `openapi.yaml`.
- `send()` and `generate()` gained `tool_choice` and `timeout`. `change_member_role` now deletes a demoted leader's thread.
- Added `seed_demo` and `SEED_USER_PASSWORD`.
- Corrected a misreading: "seeded data only" was never a restriction. See `.claude/rules/ai.md`.
- At the user's request, added a push-only WebSocket at `/api/v1/ws/` for chat and notifications, replacing polling. Channels and Daphne, one process, in-memory layer, no Redis. Published as BE-007. Prod's start command is now Daphne, and `CONN_MAX_AGE` is 0. Decisions are in `.claude/rules/api.md`, limits in `api-limits.md`.
- With the user's approval: `migrate assistant` and `seed_demo` ran on `main`, and 15 Gemini requests were spent. `main` now has 5 users, the Demo Team of 4, 10 tasks, 3 comments and 3 messages. Both test threads were cleared.

## Verification

- Phase 4: the full suite ran 442 passed, against faked Gemini on the test branch. Only the system prompt's wording changed after that, and the assistant and AI test files were rerun, not the whole suite. Ruff, `makemigrations --check` and `spectacular --validate --fail-on-warn` are clean. `openapi.yaml` gained 138 lines and lost none.
- 20 of 20 deliberate breaks were caught, each removing one safeguard, including role scoping, thread privacy and each cache rule. One break first produced invalid Python and was redone. The django-reviewer pass found one defect, now fixed: `get_task` cut the description it promised in full.
- Live, on `runserver` with real JWTs and real Gemini, as a leader and a member, 15 requests, all `succeeded`: snapshot answers, the cache spending no request, tools, history replay without thought steps, `tool_choice: "none"` after function steps, `is_error`, 401 with no token, and `DELETE`. Answers were read by hand and match the seeded data. A member got none of a teammate's work, even when told to ignore its instructions.
- That run found a real bug the check first passed: the prompt made the model refuse the asker's own request. Fixed and retested live. The member and injection questions ran on the old wording, but their limits are enforced in Python.
- Socket: the full suite ran 462 passed after the last code change, and ruff, migrations and the schema check are clean. 12 of 12 deliberate breaks were caught.
- Socket, on real Daphne with real `websockets` clients and a throwaway SQLite file, so `main` wasn't touched: a real cookie login connected, and a message arrived in 297 ms with the same shape as REST. A stranger heard nothing, a removed member stopped hearing on an open socket, and a login cookie from another origin was refused.
- Not tested: text planted in a comment against the live model, `check --deploy`, a real browser or phone on the socket, Daphne on Linux, and sockets on Neon rather than SQLite, apart from the test suite.

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

1. User commits this session's changes.
2. Phase 5: RAG. The user wants it to work from the signed-in user's actual data, like the chatbot. The tool loop and scoping are ready to reuse. Set `SEED_USER_PASSWORD` in `.env` and rerun `seed_demo` before anyone logs in as a demo account.
3. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
4. Mobile must confirm on a device that `Authorization` reaches the socket. The React Native JavaScript passes headers through, but its native layers weren't checked. `gunicorn` is unused now, so remove it when the host is chosen.
5. For Phase 8 (deployment): the user must decide how scheduled notifications reach sockets (see `.claude/rules/scheduling.md`). The host must run one always-on Daphne process, and its `/api/*` proxy must forward WebSocket upgrades. Hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api-limits.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`.

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

- 2026-11-02: error codes, request IDs and a route guard test added before Phase 4.
- 2026-11-02: Phase 4 chatbot built, migrated, seeded, checked live and ticked.
- 2026-11-02: live socket for chat and notifications added.
