# TODO

What's left to do. For what exists today, see [README.md](README.md). Per-agent progress is in [docs/status.md](docs/status.md).

## Before Phase 1

- [x] In `backend/.env`, put `-pooler` back in `DATABASE_URL`, add `connect_timeout=5`, and add `DIRECT_URL` with the direct host

## Backend

- [x] Phase 1: models, migrations and admin, including team membership and Expo device tokens, plus CI running tests and ruff
- [x] Phase 2: auth, roles, scoping, team management, core task, comment, chat and notification endpoints, stats, JSON-only responses in prod, throttled login, pagination, health checks
- [ ] Clear the GitHub billing lock and run the Backend workflow, which has never run
- [x] Phase 3: AI provider layer, rate limiting and call logging
- [x] Set the `AI_REQUESTS_*` limits in `backend/.env`
- [x] Decide what data the chatbot sends to Gemini: the signed-in user's actual data. Seeded data is only test data
- [x] Phase 4: chatbot: snapshot, tools and answer cache
- [x] Live socket for chat and notifications, with polling only as a fallback
- [x] Phase 5: RAG with pgvector
- [x] Set the `AI_EMBEDDING_*` limits in `backend/.env`
- [x] Decide what team text may go to Google: fine on free-tier terms while this is a take-home project. Revisit before real teams use it
- [ ] Phase 6: monthly AI reports
- [ ] Phase 7: seed data and final coverage
- [ ] Phase 8: deployment and event pipeline: email via Resend, Expo push, and scheduled jobs running inside the server process (D-016)

## Backend hardening

- [x] Separate `/healthz` and `/readyz`, with `/healthz` not touching the database
- [x] Correlation IDs on every request and log line
- [x] Stable error codes through one global exception handler
- [x] A test that requires a login on every route not listed as public
- [ ] Rollback steps and a smoke-check list in the deploy instructions
- [ ] Dependency vulnerability scan in CI
- [ ] Remove the generated boilerplate docstrings in `backend/config/`

## Web

- [ ] Create `web/` with its own `CLAUDE.md`, under 50 lines
- [ ] Build the app against `docs/api/`

## Mobile

- [ ] Create `mobile/` with its own `CLAUDE.md`, under 50 lines
- [ ] Build the app against `docs/api/`

## Shared

- [ ] Decide who owns `packages/api-client` and how it's generated
- [ ] Start each new agent's `CLAUDE.md` with: never commit, stay in your own folder, talk to other agents only through `docs/`
