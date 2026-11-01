# Decision Log

Append new decisions at the bottom. To change one, add a new entry that supersedes it.

| ID | Date | Decision |
|----|------|----------|
| D-001 | 2026-11-01 | Business logic lives in service modules, not in views, serializers or signals. |
| D-002 | 2026-11-01 | No Celery, no Redis, no LangChain. Scheduled work = idempotent management commands triggered by a GitHub Actions cron calling a secret-protected endpoint. Triggering is external; logic lives in Django. |
| D-003 | 2026-11-01 | Side effects (email, push, notifications, re-embedding) run via `transaction.on_commit`. |
| D-004 | 2026-11-01 | Every query returning tasks, comments, messages or stats is scoped by role and team in Python — never by the LLM (Large Language Model), never by the frontend. |
| D-005 | 2026-11-01 | The LLM never writes SQL (Structured Query Language) and never touches the database; it only calls typed tool functions. |
| D-006 | 2026-11-01 | Free-tier rule for the LLM: requests are scarce, tokens are cheap — trade tokens for requests. |
| D-007 | 2026-11-01 | Secrets only from environment variables; commit `.env.example`, never `.env`. |
| D-008 | 2026-11-01 | Datetimes stored in UTC; each team has a timezone (default "Africa/Cairo"). |
| D-009 | 2026-11-01 | Backend runs on Python 3.11: the user kept the existing `.venv` instead of the planned 3.12+. Django stays on 5.x because Django 6 requires Python 3.12. |
| D-010 | 2026-11-01 | Each agent's rules, permissions and skills are encapsulated in its own working directory to fit its technology. There is no shared root `.claude/`. |
| D-011 | 2026-11-01 | There is no root `CLAUDE.md`. Each part keeps its rules in its own `<dir>/CLAUDE.md`, under 50 lines, because agents don't read past that. The root holds `README.md` and `TODO.md`. |
| D-012 | 2026-11-01 | Only the user commits and pushes. Agents never do, whatever a ritual or skill says. |
| D-013 | 2026-11-01 | Neon connections: the app uses the pooled URL, migrations use the direct URL, and tests use a separate branch on a direct URL. `main` serves both dev and prod, by the user's decision. |
| D-014 | 2026-11-01 | An agent's `brain.md` is only an index. Facts live in small path-scoped files in `.claude/rules/`, which load by themselves on matching files, and a new topic gets a new region plus one index row. Rules that prevent real damage stay in `CLAUDE.md`. |
| D-015 | 2026-11-01 | Supersedes D-002's trigger; the rest of D-002 stands. Scheduled work stays idempotent management commands, but one scheduler process (`manage.py run_scheduler`) beside the Django server triggers them, with the schedule in code. There is no cron endpoint. GitHub Actions is for CI/CD only, and no product feature depends on it. The host must therefore stay on. |
