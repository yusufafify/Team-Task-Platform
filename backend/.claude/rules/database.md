---
paths:
  - "apps/**/models.py"
  - "apps/**/migrations/**"
  - "config/settings/*.py"
  - "manage.py"
  - ".env.example"
---

# Database

Neon branches, connections and migrations.

- Neon branches: `main` serves both local work and prod, by the user's decision, and `test` hosts pytest's temporary `test_neondb`. `config/settings/test.py` reads `TEST_DATABASE_URL` with no fallback, and refuses a pooled host or the `DATABASE_URL` endpoint.
- Neon connections follow the Elyria project: the app uses pooled `DATABASE_URL`, with `DISABLE_SERVER_SIDE_CURSORS` on because the pooler runs in transaction mode. `manage.py` swaps in `DIRECT_URL` for `migrate`, falling back to `DATABASE_URL`. gunicorn and pytest never pass through that swap. `TEST_DATABASE_URL` stays direct.
- Prod reuses connections to the pooler for 60 seconds with health checks. Set `CONN_MAX_AGE` to 0 if chat moves to ASGI.
- `AUTH_USER_MODEL` is `accounts.User`. Swapping the user model after the first migration is painful.
- A migration reaches each branch in its own step: `pytest` applies it for tests, and `migrate` updates `main`. There's no separate dev database, so a local `migrate` or data change reaches prod.
- After the first `migrate`, run `uv run python manage.py createcachetable`, or database cache calls fail.
- Keep `TEST_DATABASE_URL` and `DIRECT_URL` on direct hosts. On the pooler, pytest's database took 2m26s and couldn't be dropped. All branches share the project's 100 free compute hours, so heavy testing can suspend prod too.
- On 2026-11-01, `pytest --create-db` lost its connection mid-migration twice, right after the URLs moved to direct hosts, then passed 6 times, including a cold start confirmed with `pg_postmaster_start_time()`. Cause unknown, and no retry was added. If it recurs, rerun and check Neon's monitoring for a compute restart. CI avoids Neon by using a local Postgres service.
