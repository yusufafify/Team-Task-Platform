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
- ✅ Phase 7: demo data now covers the last complete month and is applied to `main`, with October's report rewritten from it; 592 tests at 99% coverage; `openapi.yaml` now has a test keeping it in step with the code; no endpoint changed; the demo accounts log in, and reports now give causes from comments and chat; the CI workflow hasn't run yet
- 🔄 Phase 8: reminders, Expo push, Resend email, report notifications and the scheduler are built and tested on a real server against the test branch, migrated to `main`, and published as BE-010. Still to do: choose a host, deploy, and try a real email and a real phone

## Web

- ✅ Setup: SPA on TanStack Start, design tokens, HTTP facade, dev proxy to the local API
- ✅ Auth, teams and members, tasks and comments, chat, live socket with fallback polling, notifications, assistant, stats, reports, account
- 🔄 Checks: `tsc`, lint, Prettier and build pass, and every screen was driven in a real browser against a local stub of the contract, on a production build. Against the real local API, only anonymous calls were tried: errors, allowed origin, proxy and socket close. Still to do: a signed-in pass against the real API
- 🔄 Deploy: live on Vercel at `https://nesma-airlines.vercel.app` (project `nesma-airlines`, Root Directory `web`, production branch `main`). Still to do: no API yet, so nobody can log in until the backend has a host and `vercel.json` proxies `/api/`; the socket can't pass Vercel's proxy, see WEB-003
- Last inbox ID processed: BE-010

## Mobile

- ⬜ Setup
