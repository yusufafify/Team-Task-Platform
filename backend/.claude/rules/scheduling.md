---
paths:
  - "apps/**/management/**"
  - "apps/**/tasks.py"
---

# Scheduling

How scheduled work runs (D-015). Nothing here is built yet; Phase 3 builds it. Emails and pushes caused by a user action don't pass through this: they go out through `transaction.on_commit`.

- One process, `manage.py run_scheduler`, runs beside gunicorn and calls idempotent management commands. Never start a scheduler inside gunicorn: each worker would run its own copy, and jobs would run several times.
- Keep the schedule in code, so the database is touched only when a job runs. Choose the library in Phase 3, and don't add one if the standard library covers the schedule.
- Run jobs at most hourly. Neon's free plan gives 100 CU-hours a month and suspends after 5 idle minutes, so at 0.25 CU, runs every 5 minutes or less keep it awake all month (about 180 CU-hours), while hourly runs use about 18. Tests share that allowance.
- The host must stay on. Render's free web service sleeps after 15 idle minutes and has no free background worker, so it can't run this reliably. Choose the host with that in mind.
- A sleep or restart skips runs. Each job selects what's due and not yet done, never one time slot, so the next run catches up.
- Two schedulers can overlap during a deploy, so enforce run-once in the database, with a unique constraint or a sent marker, not by timing.
- Schedule simplejwt's `flushexpiredtokens` daily. The token tables grow with every login and refresh, and nothing else clears them.
