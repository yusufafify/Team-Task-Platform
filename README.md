# Team Task Platform

A team communication and task management platform with workflow automation, an AI chatbot and AI monthly reports, on web and mobile. It's a take-home project judged on functionality, automation, AI integration, mobile quality, security, user experience, code quality and reliability.

## What it does

- **Leaders** create, assign, edit and delete team tasks, and see all team data and every member's stats.
- **Members** see and update only the tasks assigned to them, post in team chat, and see only their own stats.
- **Automation** sends email and push notifications and runs scheduled jobs.
- **AI** answers questions about the team's work and writes monthly reports. It only calls typed, team-scoped tools and never touches the database directly.

## What's in the repository

| Path | Contents | State |
|---|---|---|
| `backend/` | Django + DRF API | Core API built: auth, teams, tasks, comments, chat, notifications and stats |
| `docs/` | Shared hub: API docs, decisions, glossary, status and agent inboxes | In use |
| `web/` | React + TanStack single-page app | Not started |
| `mobile/` | Expo React Native app | Not started |
| `packages/api-client/` | Generated API client | Not started |

See [TODO.md](TODO.md) for what's next.

## Stack

- **Backend:** Python 3.11, Django 5.2 LTS, Django REST Framework, JWT auth, with `HttpOnly` cookies on web and encrypted device storage on mobile
- **Database:** PostgreSQL with pgvector on Neon
- **Web:** React, TanStack
- **Mobile:** Expo React Native
- **Automation:** Management commands run by one `run_scheduler` process beside the Django server, with no Celery or Redis

## Getting started

Backend setup is in [backend/README.md](backend/README.md).

## How the work is organized

Each part has its own agent, with its rules in `<dir>/CLAUDE.md`, kept under 50 lines. There is no root `CLAUDE.md`. Agents talk to each other only through `docs/`: see [docs/README.md](docs/README.md). Decisions are logged in [docs/decisions.md](docs/decisions.md), and domain terms are in [docs/glossary.md](docs/glossary.md).

Only the project owner commits and pushes. Agents never do.
