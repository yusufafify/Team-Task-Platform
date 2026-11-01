# TODO

What's left to do. For what exists today, see [README.md](README.md). Per-agent progress is in [docs/status.md](docs/status.md).

## Before Phase 1

- [ ] In `backend/.env`, put `-pooler` back in `DATABASE_URL`, add `connect_timeout=5`, and add `DIRECT_URL` with the direct host

## Backend

- [ ] Phase 1: models, migrations and admin, including team membership and Expo device tokens, plus CI running tests and ruff
- [ ] Phase 2: auth, roles, scoping, team management, core task, comment, chat and notification endpoints, stats, JSON-only responses in prod, throttled login, pagination, health checks
- [ ] Phase 3: deployment and event pipeline: email via Resend, Expo push, scheduled jobs, cron endpoint and GitHub workflow
- [ ] Phase 4: AI provider layer, rate limiting and call logging
- [ ] Phase 5: chatbot: snapshot, tools and answer cache
- [ ] Phase 6: RAG with pgvector
- [ ] Phase 7: monthly AI reports
- [ ] Phase 8: seed data and final coverage

## Backend hardening

- [ ] Separate `/healthz` and `/readyz`, with `/healthz` not touching the database
- [ ] Correlation IDs on every request and log line
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
