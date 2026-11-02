# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 5 are ticked, with CI deferred. Phase 6 (monthly AI reports) is next.
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 5 from the roadmap line, with no detailed prompt: a `search` tool on the existing tool loop. Design is in `.claude/rules/retrieval.md`.
- New `apps/assistant/retrieval.py`, `Embedding` model, `manage.py embed_pending`. `embed()` joined `generate()` in the gateway, and the limits now count per model, with `AI_EMBEDDING_*` settings of their own.
- The user chose search-time embedding over `on_commit`. Recorded as D-017, which supersedes D-003 for re-embedding, and the `CLAUDE.md` line changed to match.
- `gemini-embedding-2` at 768 dimensions, chosen by probing both models. One request holds documents and a query. No vector index, on purpose.
- No endpoint changed, so no changelog entry or inbox notice. The generated schema matches `docs/api/openapi.yaml` exactly.
- With the user's approval: `migrate` and `embed_pending` ran on `main`, and all 16 Demo Team items are embedded. Test threads were cleared, and the Demo Team has none.
- Gemini use: 20 requests through the app, logged in `AICall` (13 chat, 7 embedding), against about 13 estimated when the user approved. Plus 5 embedding requests in direct probes with made-up text, not logged.

## Verification

- Full suite: 525 passed. Only the `search` tool's description changed after that, and the retrieval and assistant test files were rerun, not the whole suite. Ruff, `makemigrations --check` and `spectacular --validate --fail-on-warn` are clean.
- 41 of 41 deliberate breaks caught, each removing one safeguard. 4 were missed at first, all real test gaps, now fixed: limits counted per model, chat from another team, ranking, and the command on a provider failure.
- The django-reviewer pass found no defects, and led to a query-count test, proved by 4 of the 41 breaks.
- Live on `main` through `services.ask`, six questions as a leader and a member, answers read by hand: a snapshot question spent no embedding request, the model chose `search` for the other five, an Arabic question found an English comment, a vector deleted first was rebuilt and matched in that same request, and a missing subject invented nothing. A member's results held nothing from a teammate's task.
- That run found a real defect: a member was told nobody had mentioned DNS, when a comment they can't see had. Fixed in the tool's description and retested live: "I found nothing about DNS access."
- Volume measured on the test branch at up to 20,000 synthetic items: search stays near 1 second, with no change needed. Figures are in `.claude/rules/retrieval.md`.
- With the user's approval, on real Daphne with real JWTs on `main`, 12 more requests: 401 with no token, 404 off the team, a search answer over HTTP, and `DELETE`. One planted comment, removed afterwards, was obeyed on none of three questions. `main` was confirmed back to 3 comments, 16 embeddings and no threads.
- One answer said "No, the project is not cancelled", which is more certain than the data allows. Left as is, because it came from one question: don't tune the prompt on one sample.
- One answer took 15.4 seconds: see `.claude/rules/retrieval.md`.

## Earlier work, still true

- Phases 3 and 4 and the socket were checked live. Details are in `.claude/rules/ai.md`, `assistant.md` and `api.md`.
- Never tested: `check --deploy`, a real browser or phone on the socket, Daphne on Linux, and sockets on Neon rather than SQLite, apart from the test suite.
- `main` has 5 users, the Demo Team of 4, 10 tasks, 3 comments and 3 messages, and 16 `Embedding` rows.

## In progress

Nothing.

## Next steps

1. User commits this session's changes.
2. Phase 6: monthly AI reports. Set `SEED_USER_PASSWORD` in `.env` and rerun `seed_demo` before anyone logs in as a demo account.
3. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
4. Mobile must confirm on a device that `Authorization` reaches the socket. The React Native JavaScript passes headers through, but its native layers weren't checked. `gunicorn` is unused now, so remove it when the host is chosen.
5. For Phase 8 (deployment): start the scheduler inside the Daphne process, as `.claude/rules/scheduling.md` decides. The host must run one always-on Daphne process, and its `/api/*` proxy must forward WebSocket upgrades, or web runs on the polling fallback until a ticket endpoint exists. Hosting must be free: the web host proxies `/api/*` to the API (see `.claude/rules/api-limits.md`). Set `DJANGO_NUM_PROXIES` counting that proxy, check `SECURE_PROXY_SSL_HEADER`, use `/healthz` for frequent probes, and schedule `flushexpiredtokens`. Run `embed_pending` once after the first deploy.

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

- 2026-11-02: error codes, request IDs and a route guard test added before Phase 4.
- 2026-11-02: Phase 4 chatbot built, migrated, seeded, checked live and ticked.
- 2026-11-02: live socket for chat and notifications added.
- 2026-11-02: Phase 5 RAG built, migrated, embedded, checked live and ticked.
