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
