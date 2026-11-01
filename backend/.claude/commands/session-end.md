---
description: Save backend state, publish API changes, and list changed paths for the user to commit
---

1. Update `.claude/handover.md`, keeping it to about 80 lines and only the last 3 sessions in History.
2. Update `.claude/brain.md` if durable facts changed, keeping it to about 150 lines by condensing rather than growing.
3. If the API changed:
   - Add an entry to `../docs/api/changelog.md`.
   - Run `uv run python manage.py spectacular --file ../docs/api/openapi.yaml`.
   - Append notices to `../docs/inbox/web.md` and `../docs/inbox/mobile.md`.
4. Update only the "Backend" section of `../docs/status.md`.
5. Don't commit or push. List the changed paths for the user, who makes every commit.
