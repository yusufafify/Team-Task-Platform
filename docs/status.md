# Status

Legend: ✅ done · 🔄 in progress · ⬜ not started. Each agent edits only its own section.

## Backend

- ✅ Folder structure, tooling and agent files
- ✅ Permission rules in `backend/.claude/settings.json`
- ✅ First commit, made by the user
- ✅ Phase 1: models, migrations, admin and CI built, migrations applied to `main`; the CI workflow hasn't run yet
- ✅ Phase 2: auth, roles, scoping, team, task, comment, chat, notification and stats endpoints, passing locally; the CI workflow hasn't run yet
- ✅ Phase 3: AI provider layer, rate limits and call logging built, passing locally and confirmed against live Gemini, migration applied to `main`; no endpoint changed; the CI workflow hasn't run yet
- ✅ Phase 4: chatbot built, passing locally and confirmed against live Gemini on a real server, migration applied to `main`, demo team seeded; endpoints published as BE-006; the CI workflow hasn't run yet
- ✅ Live socket for chat and notifications, at the user's request: published as BE-007; checked on a real server with real sockets; not yet tried from a real browser or phone
- ✅ Phase 5: RAG: search tool built, passing locally and confirmed against live Gemini, migration applied to `main`, demo team embedded; no endpoint changed; the CI workflow hasn't run yet
- ✅ Phase 6: monthly AI reports: `generate_reports` command and `GET teams/{id}/reports/` built, passing locally and confirmed against live Gemini on a real server, migration applied to `main`, first report written; published as BE-009; run by hand until Phase 8 schedules it; the CI workflow hasn't run yet
- ⬜ Phase 7: seed data, tests, schema export
- ⬜ Phase 8: deployment, event pipeline and scheduled jobs

## Web

- ⬜ Setup

## Mobile

- ⬜ Setup
