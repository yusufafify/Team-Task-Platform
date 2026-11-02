# Roadmap

Each future phase will come with its own detailed prompt. Every phase ships its own tests. Every API change ships its changelog entry, `openapi.yaml` and inbox notices.

- [x] Phase 1: models + migrations + admin, including team membership and Expo device tokens + CI running tests and ruff
- [x] Phase 2: auth + roles + scoping + team management + core task/comment/chat/notification + stats endpoints; JSON-only responses in prod, throttled login, pagination, health check
- [x] Phase 3: AI provider layer + rate limiting + call logging
- [x] Phase 4: chatbot: snapshot + tools + answer cache
- [x] Phase 5: RAG (Retrieval-Augmented Generation) with pgvector
- [ ] Phase 6: monthly AI reports
- [ ] Phase 7: seed data + final coverage
- [ ] Phase 8: deployment + event pipeline: email via Resend, Expo push, scheduled jobs + `run_scheduler` process

Phase 6 ships reports as a management command run by hand, because `run_scheduler` doesn't exist until Phase 8, which adds it to the schedule.

Open: no agent owns `packages/api-client`, and no phase generates it.

Open: Phases 1 to 5 were ticked without a CI run, because a GitHub billing lock stops the workflow.
