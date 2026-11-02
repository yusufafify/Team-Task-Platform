---
paths:
  - "tests/**"
  - "config/settings/test.py"
  - "pyproject.toml"
---

# Testing

How pytest is set up, and the rules that keep it away from real data.

- pytest uses `--ds` in `addopts`, because a real `DJANGO_SETTINGS_MODULE` variable beats the ini option. The `DATABASE_URL` endpoint guard runs only when that variable is set, so CI can use a local Postgres.
- pytest keeps `test_neondb` between runs (`--reuse-db`), and Django still applies new migrations on every run. Use `uv run pytest --create-db` only after editing an already-applied migration, because it drops and recreates the database.
- Don't point pytest at an existing database with a no-op `django_db_setup`. Real tables then get cleared by `transaction=True` tests.
- Use the `db` fixture only where a test needs the database.
- `tests/conftest.py` gives API tests `api`, `team`, `leader`, `member` and `outsider`. `outsider` leads another team, so a leak shows up even for a privileged role.
- `transaction.on_commit` callbacks don't run inside a test's transaction. Wrap the call in `django_capture_on_commit_callbacks(execute=True)`.
- Socket tests run through `async_to_sync`, so `database_sync_to_async` stays on the test's thread and transaction. `tests/test_realtime.py` patches out `close_old_connections`, which would otherwise close that connection. Don't use `transaction=True` there: each reconnect risks the Neon stall below.
- Test settings use the MD5 hasher, because the real one is slow by design. The suite took 8.5 minutes on Neon for 442 tests (2026-11-02), so run a single file while working.
- `tests/test_environment.py` copies `config` and `apps` into a temp folder. A new top-level package that settings import must join that list.
- A new connection to the Neon test branch can stall for minutes (seen 2026-11-02: 23 to 270 seconds, stuck in psycopg's connect, while the other threads took 1 second). Keep threaded tests small, and don't let them depend on short time windows.
- CI is `.github/workflows/backend.yml`: ruff and pytest on `pgvector/pgvector:pg18`, matching Neon's major version. Action versions are pinned by commit.
- Two pytest runs at once share `test_neondb`, so run one at a time.
- Coverage isn't a dependency: `uv run --with pytest-cov pytest --cov=apps --cov=config --cov-branch --cov-report=term-missing:skip-covered`. `prod.py` reads 0% and `test.py` misses its guards only because `tests/test_environment.py` runs them in a subprocess, which coverage can't see. Left uncovered on purpose: `__str__` methods, and `wsgi.py`, which nothing runs.
- `tests/test_api_platform.py` walks the URL table, so a new route is checked with no new test: it must refuse a stranger, and anything under a team or task must hide from another team's leader. It also fails when `docs/api/openapi.yaml` is behind the code.
