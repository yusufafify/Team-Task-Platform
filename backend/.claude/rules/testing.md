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
- Test settings use the MD5 hasher, because the real one is slow by design. The suite takes about 3 minutes on Neon.
- `tests/test_environment.py` copies `config` and `apps` into a temp folder. A new top-level package that settings import must join that list.
- CI is `.github/workflows/backend.yml`: ruff and pytest on `pgvector/pgvector:pg18`, matching Neon's major version. Action versions are pinned by commit.
