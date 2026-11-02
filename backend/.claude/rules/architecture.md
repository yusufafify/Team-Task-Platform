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

- Phase 1: five apps with models, initial migrations and admin. Apps have no `apps.py`, because Django's default config is enough.
- Phase 2: `services.py`, `serializers.py`, `views.py` and `urls.py` in all five apps, under `/api/v1/`, with no schema change. Stats sit in `apps/tasks`.
- Phase 3: `apps/ai` holds the provider, limits and call log. It has no endpoints yet, so the API didn't change.
- Dependency direction: `tasks` services import `notifications` and `teams` services. `teams` and `notifications` services import only `tasks.models`, which avoids a cycle.
- Settings split: `base.py` holds shared values. `dev.py` and `prod.py` set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES` and `CORS_ALLOWED_ORIGINS`.
- `DJANGO_SETTINGS_MODULE` in `.env` chooses dev or prod. `config/__init__.py` loads `.env` first, and `manage.py`, `wsgi.py` and `asgi.py` have no default, so they refuse to start without it. A variable set on the host wins over `.env`. pytest is pinned to `config.settings.test` in `pyproject.toml`.
- Prod logs to the console at WARNING and up, with time, level and logger name, because Django's default console handler needs DEBUG on.
- DRF defaults: cookie then Bearer JWT authentication, `TrustedOrigin` and `IsAuthenticated`, drf-spectacular schema class, JSON-only, page size 20, throttle rates. `AUTH_COOKIE_SECURE` is off only in dev. Access tokens last 15 minutes, refresh tokens 7 days and rotate.
- Cache: database backend, table `django_cache`.
- Static files: whitenoise, with compressed manifest storage in prod only.
- A blank environment variable is removed in `base.py`, so it behaves as unset. Prod then refuses to start if it's required.
- `manage.py` imports `config` only to load `.env`. Removing that import stops it seeing `DJANGO_SETTINGS_MODULE`.

## File map

- `config/settings/`: settings package.
- `config/urls.py`: admin, health checks, `/api/v1/` and the JSON error handlers. `config/views.py`: those handlers and the health views.
- `apps/README.md`: what each app holds, and the one-app-per-domain rule.
- `tests/factories.py`: shared factories. `tests/test_smoke.py`: settings load, and models match migrations.
- `pyproject.toml`: dependencies, pytest and ruff config.
- `.env.example`: every environment variable, with a comment each.

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
| `AI_MODEL` | Default `gemini-3.5-flash-lite` | Same |
| `AI_REQUESTS_PER_MINUTE` | Default 10 | Same |
| `AI_REQUESTS_PER_DAY` | Default 200 | Same |
| `AI_REQUESTS_PER_USER_PER_DAY` | Default 30 | Same |
