# Backend

Django + DRF API for the team task-management platform. Run every command below from `/backend` in PowerShell.

## Prerequisites

- [uv](https://docs.astral.sh/uv/)
- Python 3.11 in `.venv`
- PostgreSQL with the pgvector extension (not needed for `check` or lint)

## Activate the virtual environment (optional)

```powershell
.venv\Scripts\Activate.ps1
```

`uv run` already uses `.venv`, so activation is only for working by hand.

## Install

```powershell
uv sync
Copy-Item .env.example .env
```

Blank values in `.env` count as unset, so the dev defaults apply until you fill them in.

## Run

```powershell
uv run python manage.py check
uv run python manage.py runserver
```

`DJANGO_SETTINGS_MODULE` in `.env` chooses the environment for `manage.py`, `wsgi.py` and `asgi.py`, and none of them start without it. A variable set on the host wins over `.env`. `pytest` always uses `config.settings.test`.

`migrate` changes the Neon `main` branch, which also serves prod. After the first run, also run `uv run python manage.py createcachetable`.

`uv run python manage.py seed_demo` creates or refreshes a demo team of four people with tasks, comments and chat, so the app has data before any client can add it. It writes to the same branch. Set `SEED_USER_PASSWORD` first, or the accounts can't log in. The leader is `mona@demo.example`, and the members are `sara@`, `omar@` and `nour@` on the same domain.

## Lint and format

```powershell
uv run ruff check
uv run ruff format
```

## Test

```powershell
uv run pytest
```

`pytest` keeps a separate `test_neondb` on the Neon test branch, so tests never touch real tables. Every run applies new migrations to it. Rebuild it only after editing a migration that was already applied:

```powershell
uv run pytest --create-db
```

`pytest` stops if `TEST_DATABASE_URL` is missing, uses a `-pooler` host, or shares an endpoint with `DATABASE_URL`.

## Databases

| Neon branch | Used by | Where its URL lives |
|---|---|---|
| `main` | Local work and production | `DATABASE_URL` and `DIRECT_URL` in `.env` and on the host |
| `test` | `pytest` only | `TEST_DATABASE_URL` in `.env` |

Local work and production share `main`, so a local `migrate` or data change reaches production. A new migration reaches each branch in its own step:

1. `uv run pytest` applies it to the test database.
2. `uv run python manage.py migrate`, or the release step on the host, updates `main`.

The first time on a branch, also run `createcachetable` after `migrate`.

The app connects through `DATABASE_URL`, the pooled `-pooler` host. `manage.py migrate` uses `DIRECT_URL`, the direct host, because Neon recommends a direct connection for migrations, and falls back to `DATABASE_URL` if it's blank. `TEST_DATABASE_URL` is always direct.

## Deploy to a host

No host is chosen yet, so these steps apply to any Linux host. Run them there, not in PowerShell.

### Set the variables

`.env` is for local work and is never committed, so a host doesn't have one. Set these in the host's environment settings instead. A variable set on the host wins over `.env`.

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.prod` |
| `DJANGO_SECRET_KEY` | A long random value, used only on this host |
| `DJANGO_ALLOWED_HOSTS` | The API hostname, such as `api.example.com` |
| `DJANGO_NUM_PROXIES` | How many proxies sit in front of the app, `0` for none. A wrong value lets clients forge their address and dodge login limits |
| `DATABASE_URL` | The pooled PostgreSQL URL on a database with pgvector. Add `sslmode=require` if the database requires SSL, and `connect_timeout=5` |
| `CORS_ALLOWED_ORIGINS` | The web app's origin with its scheme, such as `https://app.example.com` |

The app refuses to start if any of these is missing. Also set `DIRECT_URL` to the same database's direct URL, so `migrate` avoids the pooler. `DJANGO_SECURE_HSTS_SECONDS` is optional: it defaults to `3600`, and you can raise it to `31536000` once HTTPS works across the whole domain. Prod logs warnings and errors to the console, so they appear in the host's log viewer. Prod reuses each connection to the pooler for 60 seconds with a health check. Generate the secret key with:

```shell
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Build

```shell
uv sync --frozen --no-dev
uv run --no-sync python manage.py collectstatic --noinput
```

`--no-sync` stops `uv run` from reinstalling the dev dependencies.

### Release

Run these before each new version goes live:

```shell
uv run --no-sync python manage.py check --deploy
uv run --no-sync python manage.py migrate
uv run --no-sync python manage.py createcachetable
```

### Start

```shell
uv run --no-sync daphne -b 0.0.0.0 -p $PORT config.asgi:application
```

Most hosts provide `$PORT`. Run exactly one server process, because the live socket's channels live in that process's memory. A second one would miss events sent through the first. `runserver` uses the same server locally.

### More than one server process

One process is the limit only because of that in-memory layer. To go past it:

1. Point `CHANNEL_LAYERS` at a shared layer. `channels_redis` is the standard one, so this is when to lift the no-Redis rule (D-002). `push()` is the only thing that sends to sockets, so no other code changes.
2. Run several Daphne processes behind a load balancer. It needs no sticky sessions, because sockets keep their state in the shared layer and the database.
3. Run the scheduler as its own `manage.py run_scheduler` process instead of inside the server.

### HTTPS

Prod redirects all HTTP traffic to HTTPS. The host must handle HTTPS in front of the app and overwrite the `X-Forwarded-Proto` header. Check this when choosing a host, because `prod.py` trusts that header.
