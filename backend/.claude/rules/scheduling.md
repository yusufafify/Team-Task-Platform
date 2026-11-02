---
paths:
  - "apps/**/management/**"
  - "apps/**/tasks.py"
---

# Scheduling

How scheduled work runs (D-015). Nothing here is built yet; Phase 8 builds it. Emails and pushes caused by a user action don't pass through this: they go out through `transaction.on_commit`.

- Planned by D-015: one process, `manage.py run_scheduler`, runs beside Daphne and calls idempotent management commands. A `notify()` from it can't reach open sockets, because the channel layer is in memory.
- Open, for the user to decide before Phase 8. Recommended: run the scheduler inside the Daphne process, in a thread, still calling the same commands. It needs no bridge, and free hosts rarely offer a second process, but it supersedes D-015. The alternative keeps a separate process and adds a bridge, such as Postgres `NOTIFY` on a direct connection. The old objection was gunicorn's several workers each running a copy. Daphne is one process, and run-once is enforced in the database anyway.
- Keep the schedule in code, so the database is touched only when a job runs. Choose the library in Phase 8, and don't add one if the standard library covers the schedule.
- Run jobs at most hourly. Neon's free plan gives 100 CU-hours a month and suspends after 5 idle minutes, so at 0.25 CU, runs every 5 minutes or less keep it awake all month (about 180 CU-hours), while hourly runs use about 18. Tests share that allowance.
- The host must stay on. Render's free web service sleeps after 15 idle minutes and has no free background worker, so it can't run this reliably. Choose the host with that in mind.
- A sleep or restart skips runs. Each job selects what's due and not yet done, never one time slot, so the next run catches up.
- Two schedulers can overlap during a deploy, so enforce run-once in the database, with a unique constraint or a sent marker, not by timing.
- Schedule simplejwt's `flushexpiredtokens` daily. The token tables grow with every login and refresh, and nothing else clears them.
