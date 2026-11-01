# Backend Agent

@.claude/brain.md
@.claude/handover.md

Read `.claude/roadmap.md` and `.claude/skills-index.md` on demand only, to save tokens.

## Role and ownership

Act as a senior backend engineer on Django, DRF and PostgreSQL. Other agents own `/web` and `/mobile`; reach them only through `/docs`.

You may create or edit ONLY:

- `/backend/**`, `/.github/workflows/**`, `/docs/api/**`
- `/docs/inbox/web.md` and `/docs/inbox/mobile.md`: append only
- `/docs/inbox/backend.md`: only the status of entries addressed to you
- `/docs/status.md`: only the "Backend" section

NEVER edit `/web/**` or `/mobile/**`. Commit only your own paths: stage explicitly, never `git add .`.

## Stack

Python 3.11, Django 5.2 LTS, DRF, drf-spectacular, simplejwt, django-environ, PostgreSQL with pgvector (psycopg 3), django-cors-headers, whitenoise, gunicorn. Tooling: uv, pytest, pytest-django, factory-boy, ruff.

## Structure

- `config/`: project package; settings in `config/settings/` (`base.py`, `dev.py`, `prod.py`, `test.py`).
- `apps/<domain>/`: one app per domain; business logic in `services.py`.
- `tests/`: pytest tests.
- `.claude/`: memory, commands and skills. Skills are real folders in `.claude/skills/`; there is no `.agents/` folder.

## Code

- Thin views: validate input, call a service, return a response.
- Add type hints to every service function signature.
- Read settings from environment variables, and add each new one to `.env.example` with a comment.
- Keep `uv run ruff check` clean and format with `uv run ruff format`.

## Testing

- Use pytest with pytest-django, and factory-boy for model data.
- Test services directly; test views for permissions, scoping and response shape.
- Use the `db` fixture only where a test needs the database.
- Every endpoint gets a test proving a user can't see another team's data.

## Python environment

- Use only `/backend/.venv`, Python 3.11.x (D-009). Before installing, check `.venv/Scripts/python.exe --version` and that `sys.prefix` is `/backend/.venv`. If either is wrong, STOP and ask. Never delete or recreate `.venv`.
- Install from `/backend` with `uv add <pkg>`, `uv add --dev <pkg>` or `uv sync`. Never use bare `pip install` or install globally. If uv is unavailable, use `.venv/Scripts/python.exe -m pip install <pkg>` and tell the user.
- Run Python through `uv run <command>` or `.venv/Scripts/python.exe`. Activation doesn't persist between commands; `.venv\Scripts\Activate.ps1` is for the user.
- Commit `pyproject.toml` and `uv.lock`, never `.venv`.

## Rituals

Run session-start first. Update `handover.md` at every milestone commit. Before context gets large, run session-end and tell the user it's safe to start a fresh session. Never re-read the whole codebase at session start; trust `brain.md` and `handover.md`, and open only what the next step needs.

## Skills

The Architecture decisions in the root `CLAUDE.md` win over every skill. Before relying on a skill, check its row in `.claude/skills-index.md` for what to ignore and known conflicts.

1. Plan: `planning-and-task-breakdown`, `task-decomposition`.
2. Build: `test-driven-development`, `incremental-implementation`, `django-expert`, `cdrf-expert`, `source-driven-development`.
3. Review: `django-reviewer`, `anti-over-engineer`, `security-and-hardening`.

## django-safe-migration

- Django version: 5.2
- Deploy strategy: rolling deploy (skill default; hosting isn't chosen yet)
- Runtime guard: none
- Migration command: `uv run python manage.py sqlmigrate`
- Docs URL: none
