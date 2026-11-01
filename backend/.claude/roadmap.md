# Roadmap

Each future phase will come with its own detailed prompt. Every phase ships its own tests. Every API change ships its changelog entry, `openapi.yaml` and inbox notices.

- [ ] Phase 1: models + migrations + admin, including team membership and Expo device tokens + CI running tests and ruff
- [ ] Phase 2: auth + roles + scoping + team management + core task/comment/chat/notification + stats endpoints; JSON-only responses in prod, throttled login, pagination, health check
- [ ] Phase 3: deployment + event pipeline: email via Resend, Expo push, scheduled jobs + `run_scheduler` process
- [ ] Phase 4: AI provider layer + rate limiting + call logging
- [ ] Phase 5: chatbot: snapshot + tools + answer cache
- [ ] Phase 6: RAG (Retrieval-Augmented Generation) with pgvector
- [ ] Phase 7: monthly AI reports
- [ ] Phase 8: seed data + final coverage

Open: no agent owns `packages/api-client`, and no phase generates it.
