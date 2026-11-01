---
description: Save backend state, publish API changes, and commit own paths
---

1. Update `.claude/handover.md`, keeping it to about 80 lines and only the last 3 sessions in History.
2. Update `.claude/brain.md` if durable facts changed, keeping it to about 150 lines by condensing rather than growing.
3. If the API changed:
   - Add an entry to `../docs/api/changelog.md`.
   - Run `uv run python manage.py spectacular --file ../docs/api/openapi.yaml`.
   - Append notices to `../docs/inbox/web.md` and `../docs/inbox/mobile.md`.
4. Update only the "Backend" section of `../docs/status.md`.
5. Commit your own paths: stage each one explicitly, never `git add .`.
