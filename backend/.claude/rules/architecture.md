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

- Phase 1: five apps with models, initial migrations and admin. No endpoints or `services.py` yet. Apps have no `apps.py`, because Django's default config is enough.
- Settings split: `base.py` holds shared values. `dev.py` and `prod.py` set `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES` and `CORS_ALLOWED_ORIGINS`.
- `DJANGO_SETTINGS_MODULE` in `.env` chooses dev or prod. `config/__init__.py` loads `.env` first, and `manage.py`, `wsgi.py` and `asgi.py` have no default, so they refuse to start without it. A variable set on the host wins over `.env`. pytest is pinned to `config.settings.test` in `pyproject.toml`.
- Prod logs to the console at WARNING and up, with time, level and logger name, because Django's default console handler needs DEBUG on.
- DRF defaults: JWT authentication, `IsAuthenticated`, drf-spectacular schema class.
- Cache: database backend, table `django_cache`.
- Static files: whitenoise, with compressed manifest storage in prod only.
- A blank environment variable is removed in `base.py`, so it behaves as unset. Prod then refuses to start if it's required.
- `manage.py` imports `config` only to load `.env`. Removing that import stops it seeing `DJANGO_SETTINGS_MODULE`.

## File map

- `config/settings/`: settings package.
- `config/urls.py`: Django's default admin route only.
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
| `DATABASE_URL` | Default `postgres://localhost:5432/nesma`, pooled host in `.env` | Required, pooled host |
| `DIRECT_URL` | Direct host, used by `migrate` | Direct host, used by `migrate` |
| `CORS_ALLOWED_ORIGINS` | Default localhost 5173, 8081 | Required |
| `DJANGO_SECURE_HSTS_SECONDS` | Unused | Default 3600 |
