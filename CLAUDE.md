# Team Task Platform: Orchestrator

## Project overview

Team communication and task management platform with workflow automation, AI chatbot, AI monthly reports, web app and mobile app. Interview take-home judged on functionality, automation, AI integration, mobile quality, security, UX (User Experience), code quality and reliability.

## Monorepo map

| Path | Contents |
|------|----------|
| `/backend` | Django + DRF (Django REST Framework) |
| `/web` | React + TanStack SPA (Single-Page Application) |
| `/mobile` | Expo React Native |
| `/docs` | Shared hub |
| `/packages/api-client` | Generated client |

## Agent map

| Agent | Owns | May also write |
|-------|------|----------------|
| backend | `/backend/**`, `/.github/workflows/**`, `/docs/api/**` | Append to `/docs/inbox/web.md` and `/docs/inbox/mobile.md`; update the status of entries addressed to it in `/docs/inbox/backend.md`; edit the "Backend" section of `/docs/status.md` |
| web | `/web/**` | Append to `/docs/inbox/backend.md` and `/docs/inbox/mobile.md`; update the status of entries addressed to it in `/docs/inbox/web.md`; edit the "Web" section of `/docs/status.md` |
| mobile | `/mobile/**` | Append to `/docs/inbox/backend.md` and `/docs/inbox/web.md`; update the status of entries addressed to it in `/docs/inbox/mobile.md`; edit the "Mobile" section of `/docs/status.md` |

Never edit another agent's paths. Commit only your own paths: stage explicitly, never `git add .`.

Each agent's detailed instructions live in `<dir>/CLAUDE.md`; its memory lives in `<dir>/.claude/brain.md` and `<dir>/.claude/handover.md`.

Each agent's rules, permissions and skills are encapsulated in its own working directory so they fit that agent's technology. Start every agent from its own directory. There is no shared root `.claude/`.

## Communication protocol

Agents communicate only through files in `/docs`. The full protocol and templates are in `/docs/README.md`.

- Send a message by appending an entry to the target agent's inbox in `/docs/inbox/`. IDs are BE-xxx, WEB-xxx and MOB-xxx.
- Entry types: notice, request, breaking-change, question. Statuses: open, accepted, done, rejected.
- Receivers update Status with a reason and fill in Resolution.
- Any change to an endpoint, payload, auth behavior or error format needs a changelog entry, a regenerated `/docs/api/openapi.yaml`, and notices in the web and mobile inboxes.

## Session rituals

- Run session-start at the beginning of every session: read handover, read new inbox entries, summarize state and plan in 5 lines, begin.
- Update handover at every milestone commit, not only at session end.
- Before context gets large, run session-end and tell the user it's safe to start a fresh session.
- Never re-read the whole codebase at session start; trust brain and handover, and open only what the next step needs.
- At session end: update handover, update brain if durable facts changed, publish any API change, update your section of status, commit your own paths.

## Architecture decisions

- Business logic lives in service modules, not in views, serializers or signals.
- No Celery, no Redis, no LangChain. Scheduled work = idempotent management commands triggered by a GitHub Actions cron calling a secret-protected endpoint. Triggering is external; logic lives in Django.
- Side effects (email, push, notifications, re-embedding) run via `transaction.on_commit`.
- Every query returning tasks, comments, messages or stats is scoped by role and team in Python — never by the LLM (Large Language Model), never by the frontend.
- The LLM never writes SQL (Structured Query Language) and never touches the database; it only calls typed tool functions.
- Free-tier rule for the LLM: requests are scarce, tokens are cheap — trade tokens for requests.
- Secrets only from environment variables; commit `.env.example`, never `.env`.
- Datetimes stored in UTC; each team has a timezone (default "Africa/Cairo").

## Glossary

- Statuses: todo, in_progress, blocked, done. Priorities: low, medium, high, urgent.
- Overdue: due date passed and status ≠ done (computed, never stored).
- Delayed: completed after its due date.
- Completion rate (period): completed in period ÷ due in period.
- On-time rate: completed on/before due ÷ all completed in period.
- Average delay: mean days late over delayed tasks.
- Leader: create/assign/edit/delete team tasks; sees all team data and every member's stats.
- Member: sees/updates only tasks assigned to them; posts in team chat; sees only own stats.
