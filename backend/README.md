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

`uv run python manage.py seed_demo` creates or refreshes a demo team of four people with tasks, comments and chat, so the app has data before any client can add it. It writes to the same branch. Set `SEED_USER_PASSWORD` first, or the accounts can't log in. The leader is `mona@demo.example`, and the members are `sara@`, `omar@` and `nour@` on the same domain. It fills the days around today and the last complete month, so `generate_reports` has a real month to write up on any date. A reseed moves those dates, but a report already written stays as it was.

`uv run python manage.py embed_pending` makes existing tasks, comments and chat searchable for the assistant. Searches do this themselves, 50 items at a time, so run it after the first migration and after changing `AI_EMBEDDING_MODEL`. It sends that text to Gemini and spends embedding requests, and it's safe to rerun.

Nothing runs on a schedule locally, because local work shares its database with production. To run a job by hand, use `send_reminders`, `deliver_pending` or `generate_reports`. They write to `main`, and they can send real email and pushes, so run them only when you mean to.

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

No host is chosen yet, so these steps apply to any host that runs a container and stays on. The host needs one always-on process, public HTTPS that overwrites `X-Forwarded-Proto`, WebSockets and outbound HTTPS.

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
| `GEMINI_API_KEY` | The Google AI Studio key |
| `RESEND_API_KEY` | A Resend key with sending access only |

The app refuses to start if any of these is missing. `DJANGO_SECURE_HSTS_SECONDS` is optional: it defaults to `3600`, and you can raise it to `31536000` once HTTPS works across the whole domain. `EMAIL_FROM` is optional too: see "Email" below. Prod logs warnings and errors to the console, so they appear in the host's log viewer. Generate the secret key with:

```shell
uv run python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### Build and start

Point the host at the `Dockerfile` in `backend/`. It installs from the lockfile, collects static files and starts Daphne on `$PORT`, or 8000 without one. `.dockerignore` keeps `.env` out of the image.

Run exactly one copy of the container, because the live socket's channels and the scheduler live in that process's memory. A second one would miss events sent through the first. `runserver` uses the same server locally.

### Release

Before a new version with a migration goes live, run this from your own machine, where `.env` holds `DIRECT_URL`. It updates `main`, which local work shares:

```powershell
uv run python manage.py migrate
```

Migrations must add before they remove, because the old version keeps serving until the new one is up. After the very first deploy, also run `embed_pending` once.

### Check it's working

1. `GET /healthz` answers 200, and `GET /readyz` answers 200. Probe only `/healthz` regularly, because `/readyz` wakes Neon.
2. The log shows no `Scheduled job ... failed` line after startup.
3. Log in, then open a socket to `/api/v1/ws/`. Assign someone else a task, and a notification arrives on their socket.
4. That person gets the email. A failed send logs `emailed_at failed` or `pushed_at failed`, with the status from Resend or Expo.
5. Confirm a request from a client shows the right address in the login limits: `DJANGO_NUM_PROXIES` must count every proxy in front of the app, including the web host's.

### Roll back

Redeploy the previous image. Migrations stay applied, which is safe as long as they only added things, because the old code ignores new columns. Never reverse a migration on `main` without a backup: Neon's point-in-time restore is the way back from bad data.

### Scheduled jobs

The server runs them itself, on its own event loop, with no separate process. Each runs at startup, then:

| Job | Every | Does |
|---|---|---|
| `send_reminders` | Hour | Due-soon and overdue notifications, once per due date |
| `deliver_pending` | Hour | Retries a day's failed email and push |
| `generate_reports` | Day | Each team's last complete month, and tells its leaders |
| `flushexpiredtokens` | Day | Clears expired refresh tokens |

A restart can't double anything, because each job selects only what's still owed. Set `SCHEDULER_IN_SERVER=false` to turn the schedule off, and never run it in more than one process.

### Email

Email goes through Resend's API, so outbound SMTP doesn't need to be open. The default sender, `onboarding@resend.dev`, reaches only the email address on the Resend account. Any other recipient is refused, and the server logs a 403 and doesn't retry. To reach everyone, verify a domain in Resend and set `EMAIL_FROM`, such as `Team Tasks <tasks@your-domain>`. The free plan allows 100 emails a day. Addresses ending in `.example`, like the seeded accounts, are skipped.

### More than one server process

One process is the limit only because of that in-memory layer. To go past it:

1. Point `CHANNEL_LAYERS` at a shared layer. `channels_redis` is the standard one, so this is when to lift the no-Redis rule (D-002). `push()` is the only thing that sends to sockets, so no other code changes.
2. Run several Daphne processes behind a load balancer. It needs no sticky sessions, because sockets keep their state in the shared layer and the database.
3. Set `SCHEDULER_IN_SERVER=false` on the servers, and run the schedule as one `manage.py run_scheduler` process. It reaches sockets only through that shared layer.

### HTTPS

Prod redirects all HTTP traffic to HTTPS. The host must handle HTTPS in front of the app and overwrite the `X-Forwarded-Proto` header. Check this when choosing a host, because `prod.py` trusts that header.
