---
paths:
  - "config/**"
  - "apps/**"
  - "manage.py"
  - ".env.example"
---

# Architecture

What's built, where it lives, and how it's configured.

## As built

- Apps are listed in `apps/README.md`, under `/api/v1/`. They have no `apps.py`, because Django's default config is enough. `apps/ai` has no endpoints, and `assistant` and `reports` both call its `generate()`.
- Dependency direction: `tasks` and `reports` services import `notifications` services. `teams` and `notifications` services import only `tasks.models`, which avoids a cycle. `assistant` imports the others' services. Only `reports` imports it, for row helpers, and only `seed_demo` imports `reports`, for `last_complete_month`.
- Settings split: `base.py` holds shared values. `dev.py` and `prod.py` set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES` and `CORS_ALLOWED_ORIGINS`.
- `DJANGO_SETTINGS_MODULE` in `.env` chooses dev or prod. `config/__init__.py` loads `.env` first, and `manage.py`, `wsgi.py` and `asgi.py` have no default, so they refuse to start without it. A variable set on the host wins over `.env`. pytest is pinned to `config.settings.test` in `pyproject.toml`.
- The server is ASGI, on Daphne in one process, for HTTP and the `/api/v1/ws/` socket. `config/asgi.py` routes both. `wsgi.py` remains but nothing runs it.
- Prod logs to the console at WARNING and up, with time, level, logger name and request ID, because Django's default console handler needs DEBUG on.
- DRF defaults: cookie then Bearer JWT authentication, `TrustedOrigin` and `IsAuthenticated`, drf-spectacular schema class, JSON-only, page size 20, throttle rates. `AUTH_COOKIE_SECURE` is off only in dev. Access tokens last 15 minutes, refresh tokens 7 days and rotate.
- Cache: database backend, table `django_cache`. Static files: whitenoise, with compressed manifest storage in prod only.
- A blank environment variable is removed in `base.py`, so it behaves as unset. Prod then refuses to start if it's required. `manage.py` imports `config` only to load `.env`. Removing that import stops it seeing `DJANGO_SETTINGS_MODULE`. `tests/test_environment.py` hides real values from its subprocesses, so a new required variable joins its `PROD_VALUES`.

## File map

- `config/urls.py`: admin, health checks, `/api/v1/` and the JSON error handlers. `config/views.py`: those handlers and the health views. `config/exceptions.py`: DRF's `EXCEPTION_HANDLER`. `config/request_id.py`: the request ID middleware and log filter. `config/scheduler.py`: the schedule.
- `tests/factories.py`: shared factories. `tests/test_smoke.py`: settings load, and models match migrations. `Dockerfile`: the prod image. `.env.example`: every environment variable, with a comment each.

## Environment variables

| Variable | Dev | Prod |
|----------|-----|------|
| `DJANGO_SETTINGS_MODULE` | Required, `config.settings.dev` | Required, `config.settings.prod` |
| `TEST_DATABASE_URL` | Required by pytest, Neon test branch | Unused |
| `DJANGO_SECRET_KEY` | Insecure default | Required |
| `DJANGO_DEBUG` | Default true | Ignored, always off |
| `DJANGO_ALLOWED_HOSTS` | Default localhost, 127.0.0.1 | Required |
| `DJANGO_NUM_PROXIES` | Unused | Required, proxies in front of the app, 0 for none |
| `DATABASE_URL` | Default `postgres://localhost:5432/nesma`, pooled host in `.env` | Required, pooled host |
| `DIRECT_URL` | Direct host, used by `migrate` | Direct host, used by `migrate` |
| `CORS_ALLOWED_ORIGINS` | Default localhost 5173, 8081 | Required |
| `DJANGO_SECURE_HSTS_SECONDS` | Unused | Default 3600 |
| `GEMINI_API_KEY` | Needed only by AI features | Required |
| `AI_MODEL`, `AI_REQUESTS_*`, `AI_EMBEDDING_*` | Defaults in `.env.example` | Same |
| `RESEND_API_KEY` | Optional, no email without it | Required |
| `EMAIL_FROM` | Default `onboarding@resend.dev`, reaches only the Resend account's owner | Same |
| `SCHEDULER_IN_SERVER` | Unused, always off | Default true |
| `SEED_USER_PASSWORD` | Optional, for `seed_demo` logins | Same |
