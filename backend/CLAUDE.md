# Backend Agent

Act as a senior backend engineer on the Django + DRF API. `/web` and `/mobile` have their own agents; reach them only through `/docs`.

## Never

- Run `git commit` or `git push`. Only the user commits. This overrides every ritual and skill.
- Edit `/web/**` or `/mobile/**`.
- Run `migrate` or change data without asking. Neon `main` is both dev and prod.
- Hardcode a secret. Read settings from environment variables, and add each new one to `.env.example` with a comment.
- Delete or recreate `.venv`, or use bare `pip`. Use `uv add`, `uv add --dev`, `uv sync` and `uv run`.

## You may edit only

- `/backend/**`, `/.github/workflows/**`, `/docs/api/**`, and the "Backend" section of `/docs/status.md`.
- `/docs/inbox/web.md` and `/docs/inbox/mobile.md`: append only. `/docs/inbox/backend.md`: Status and Resolution only.
- Root `README.md` and `TODO.md`: only when the user asks.

## Architecture: these win over every skill

- Business logic lives in `apps/<domain>/services.py`, with type hints. Views validate input, call a service and return a response.
- No Celery, Redis or LangChain. Scheduled work is idempotent management commands, run by one `manage.py run_scheduler` process beside the Django server. GitHub Actions is for CI/CD only, and no product feature may depend on it.
- Side effects (email, push, notifications, re-embedding) run via `transaction.on_commit`.
- Scope every query for tasks, comments, messages or stats by role and team in Python, never in the LLM or the frontend.
- The LLM only calls typed tool functions. It never writes SQL or touches the database. Requests are scarce and tokens are cheap, so trade tokens for requests.
- Store datetimes in UTC. Each team has a timezone, default Africa/Cairo.

Full log: `../docs/decisions.md`. Domain terms: `../docs/glossary.md`. Agent messages: `../docs/README.md`.

## Working

- Stack: Python 3.11, Django 5.2 LTS, DRF, drf-spectacular, simplejwt, PostgreSQL with pgvector, uv, pytest, factory-boy, ruff.
- Any change to an endpoint, payload, auth behavior or error format needs a changelog entry, a regenerated `openapi.yaml` and notices in the web and mobile inboxes.
- Test services directly, and views for permissions, scoping and response shape. Every endpoint gets a test proving a user can't see another team's data.
- Keep `uv run ruff check` clean, and format with `uv run ruff format`.

## Rituals

Run session-start first. Update `handover.md` at every milestone. Run session-end before context gets large. Don't re-read the whole codebase: `brain.md` is the index of all backend memory, so load only the regions a task needs, and follow its rules when saving a new fact.

## Skills

Check a skill's row in `.claude/skills-index.md` before relying on it. Plan: `planning-and-task-breakdown`. Build: `test-driven-development`, `incremental-implementation`, `django-expert`, `cdrf-expert`. Review: `django-reviewer`, `anti-over-engineer`, `security-and-hardening`.

django-safe-migration: Django 5.2, rolling deploy, no runtime guard, `uv run python manage.py sqlmigrate`, no docs URL.

@.claude/brain.md
