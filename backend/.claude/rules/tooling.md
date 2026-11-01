---
paths:
  - "pyproject.toml"
  - "uv.lock"
  - ".python-version"
---

# Tooling

Commands, the Python environment and tool quirks.

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

## Notes

- Python 3.11 was kept (D-009), so Django stays on 5.x.
- Before installing, check `.venv/Scripts/python.exe --version` and that `sys.prefix` is `/backend/.venv`. If either is wrong, stop and ask. If uv is unavailable, use `.venv/Scripts/python.exe -m pip install <pkg>` and tell the user.
- Ruff runs rules E, F, I, UP, B and DJ at line length 100.
- Ruff excludes `.claude`, because installed skills ship files that fail lint and format checks.
- gunicorn can't run on Windows. Use `runserver` locally; gunicorn is for the Linux deployment.
- `uv.exe` is in `%USERPROFILE%\.local\bin`. A shell started before the install may not see it until restarted.
- uv's "Failed to hardlink" warning is harmless: its cache is on C: and the project on D:.
