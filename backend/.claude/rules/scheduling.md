---
paths:
  - "apps/**/management/**"
  - "apps/**/tasks.py"
---

# Scheduling

How scheduled work runs (D-015, D-016). Nothing here is built yet; Phase 8 builds it. Emails and pushes caused by a user action don't pass through this: they go out through `transaction.on_commit`.

- D-016 supersedes D-015's separate process for now. The schedule loop is one function that calls idempotent management commands, and it must reach sockets, because real-time features use them.
- One server process, as now: `config/asgi.py` starts that function in a daemon thread when a setting is on. Daphne has no ASGI `lifespan`, so nothing else can hook startup. `notify()` then works with no bridge, and free hosts rarely offer a second process.
- Several server processes: turn that setting off and run `manage.py run_scheduler`, which calls the same function. It needs the shared layer from "Deploy to a host" in `README.md`. Never leave the setting on in more than one process.
- Rejected: a separate process plus a bridge such as Postgres `NOTIFY`, which adds a direct connection and more to break. The old objection to running in the server was gunicorn's several workers each running a copy, which doesn't apply to one Daphne process.
- Keep the schedule in code, so the database is touched only when a job runs. Choose the library in Phase 8, and don't add one if the standard library covers the schedule.
- Run jobs at most hourly. Neon's free plan gives 100 CU-hours a month and suspends after 5 idle minutes, so at 0.25 CU, runs every 5 minutes or less keep it awake all month (about 180 CU-hours), while hourly runs use about 18. Tests share that allowance.
- The host must stay on. Render's free web service sleeps after 15 idle minutes and has no free background worker, so it can't run this reliably. Choose the host with that in mind.
- A sleep or restart skips runs. Each job selects what's due and not yet done, never one time slot, so the next run catches up.
- Two schedulers can overlap during a deploy, so enforce run-once in the database, with a unique constraint or a sent marker, not by timing.
- Schedule simplejwt's `flushexpiredtokens` daily. The token tables grow with every login and refresh, and nothing else clears them.
- `embed_pending` is optional here: searches embed as they go, so it only shortens a backlog. Hourly at most, and each run with work to do spends embedding requests.
