# Backend Brain

Durable facts only. Hard cap about 150 lines: condense rather than grow.

## Scope

Django + DRF API for the team task-management platform. Ownership rules are in `CLAUDE.md`.

## As-built architecture

- Skeleton only: no project apps, models, endpoints or business logic yet.
- Settings split: `base.py` holds shared values. `dev.py` and `prod.py` set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES` and `CORS_ALLOWED_ORIGINS`.
- `DJANGO_SETTINGS_MODULE` in `.env` chooses dev or prod. `config/__init__.py` loads `.env` first, and `manage.py`, `wsgi.py` and `asgi.py` have no default, so they refuse to start without it. A variable set on the host wins over `.env`. pytest is pinned to `config.settings.test` in `pyproject.toml`.
- Neon branches: `main` serves both local work and prod, by the user's decision, and `test` hosts pytest's temporary `test_neondb`. `config/settings/test.py` reads `TEST_DATABASE_URL` with no fallback, and refuses a pooled host or the `DATABASE_URL` endpoint.
- Prod logs to the console at WARNING and up, with time, level and logger name, because Django's default console handler needs DEBUG on.
- Neon connections follow the Elyria project: the app uses pooled `DATABASE_URL`, with `DISABLE_SERVER_SIDE_CURSORS` on because the pooler runs in transaction mode. `manage.py` swaps in `DIRECT_URL` for `migrate`, falling back to `DATABASE_URL`. gunicorn and pytest never pass through that swap. `TEST_DATABASE_URL` stays direct.
- Prod reuses connections to the pooler for 60 seconds with health checks. Set `CONN_MAX_AGE` to 0 if chat moves to ASGI.
- pytest uses `--ds` in `addopts`, because a real `DJANGO_SETTINGS_MODULE` variable beats the ini option. The `DATABASE_URL` endpoint guard runs only when that variable is set, so CI can use a local Postgres.
- DRF defaults: JWT authentication, `IsAuthenticated`, drf-spectacular schema class.
- Cache: database backend, table `django_cache`.
- Static files: whitenoise, with compressed manifest storage in prod only.

## File map

- `config/settings/`: settings package.
- `config/urls.py`: Django's default admin route only.
- `apps/README.md`: planned apps and the one-app-per-domain rule.
- `tests/test_smoke.py`: checks that settings load.
- `pyproject.toml`: dependencies, pytest and ruff config.
- `.env.example`: every environment variable, with a comment each.
- `.claude/`: memory, roadmap, commands, skills, permission rules.
- `.claude/skills-index.md`: skills table and conflict lists, read on demand.
- `graphify-out/`: gitignored knowledge graph of `/backend`. Refresh it with `/graphify . --update`, run from `/backend`. `.graphifyignore` keeps `.claude/` and `skills-lock.json` out, because 270 of the 296 detected files were installed skills.

## Conventions

See `CLAUDE.md`. Ruff runs rules E, F, I, UP, B and DJ at line length 100. Use the `db` fixture only where a test needs the database.

Skills last synced 2026-11-01 by /sync-skills: 35 usable.

## Decisions

The rules are in `CLAUDE.md`. The full log, with the D-xxx IDs that `skills-index.md` cites, is `/docs/decisions.md`. Python 3.11 was kept (D-009), so Django stays on 5.x.

## Environment variables

| Variable | Dev | Prod |
|----------|-----|------|
| `DJANGO_SETTINGS_MODULE` | Required, `config.settings.dev` | Required, `config.settings.prod` |
| `TEST_DATABASE_URL` | Required by pytest, Neon test branch | Unused |
| `DJANGO_SECRET_KEY` | Insecure default | Required |
| `DJANGO_DEBUG` | Default true | Ignored, always off |
| `DJANGO_ALLOWED_HOSTS` | Default localhost, 127.0.0.1 | Required |
| `DATABASE_URL` | Default `postgres://localhost:5432/nesma`, pooled host in `.env` | Required, pooled host |
| `DIRECT_URL` | Direct host, used by `migrate` | Direct host, used by `migrate` |
| `CORS_ALLOWED_ORIGINS` | Default localhost 5173, 8081 | Required |
| `DJANGO_SECURE_HSTS_SECONDS` | Unused | Default 3600 |

## Commands

Run from `/backend`.

```powershell
uv sync                                  # install from the lockfile into .venv
uv add <pkg>                             # add a dependency
uv add --dev <pkg>                       # add a dev dependency
uv pip list                              # list what's in .venv
uv run python manage.py check            # system checks
uv run python manage.py runserver        # dev server
uv run pytest                            # tests
uv run pytest --create-db                # tests, after editing an applied migration
uv run ruff check                        # lint
uv run ruff format                       # format
uv run python manage.py spectacular --file ../docs/api/openapi.yaml   # schema export
.venv/Scripts/python.exe --version       # verify the interpreter
```

## Gotchas

- Do not run `migrate` until Phase 1 sets `AUTH_USER_MODEL`. Swapping the user model after the first migration is painful.
- A migration reaches each branch in its own step: `pytest` applies it for tests, and `migrate` updates `main`. There's no separate dev database, so a local `migrate` or data change reaches prod.
- pytest keeps `test_neondb` between runs (`--reuse-db`), and Django still applies new migrations on every run. Use `uv run pytest --create-db` only after editing an already-applied migration, because it drops and recreates the database.
- Don't point pytest at an existing database with a no-op `django_db_setup`. Real tables then get cleared by `transaction=True` tests.
- Keep `TEST_DATABASE_URL` and `DIRECT_URL` on direct hosts. On the pooler, pytest's database took 2m26s and couldn't be dropped. All branches share the project's 100 free compute hours, so heavy testing can suspend prod too.
- On 2026-11-01, `pytest --create-db` lost its connection mid-migration twice, right after the URLs moved to direct hosts, then passed 6 times, including a cold start confirmed with `pg_postmaster_start_time()`. Cause unknown, and no retry was added. If it recurs, rerun and check Neon's monitoring for a compute restart. Phase 1 CI should use a local Postgres service.
- After the first `migrate`, run `uv run python manage.py createcachetable`, or database cache calls fail.
- gunicorn can't run on Windows. Use `runserver` locally; gunicorn is for the Linux deployment.
- `uv.exe` is in `%USERPROFILE%\.local\bin`. A shell started before the install may not see it until restarted.
- uv's "Failed to hardlink" warning is harmless: its cache is on C: and the project on D:.
- A blank environment variable is removed in `base.py`, so it behaves as unset. Prod then refuses to start if it's required.
- `manage.py` imports `config` only to load `.env`. Removing that import stops it seeing `DJANGO_SETTINGS_MODULE`.
- In `.claude/settings.json`, `/path` anchors at the working directory (`backend/`), and `../web/**` silently matches nothing (tested). The `/web` and `/mobile` rules use `//**/Nesma-Airlines/...`, so renaming the repo folder disables them.
- Deny beats allow. A `!` carve-out works only on bare or `./` deny rules listed before it in the same file (tested), so the `.env.*` rules are bare and cover `backend/` only. In `/web` and `/mobile`, only an exact `.env` is denied.
- Before installing, check `.venv/Scripts/python.exe --version` and that `sys.prefix` is `/backend/.venv`. If either is wrong, stop and ask. If uv is unavailable, use `.venv/Scripts/python.exe -m pip install <pkg>` and tell the user.
- Keep `CLAUDE.md` under 50 lines, because agents don't read past that. There is no root `CLAUDE.md`, by the user's decision (D-011). `.claude/rules/` files without `paths` frontmatter load every session, and `@` imports load with `CLAUDE.md`, so bulky reference text belongs in an on-demand file like `skills-index.md`.
- Ruff excludes `.claude`, because installed skills ship files that fail lint and format checks.
- Skills are real folders in `.claude/skills/`; the user doesn't want an `.agents/` folder. The skills installer appears to recreate `.agents/` and link into it, so copy skills in by hand.
- `gemini-api-dev` was copied from `google-gemini/gemini-skills` at commit `39d81f4`. `resend` and `email-best-practices` were copied from `resend/resend-skills` at commit `b2ae7b1`.
- Read and Edit deny rules were tested on built-in file tools only. They don't stop a Python script that opens files itself, including one started through `uv run`.
