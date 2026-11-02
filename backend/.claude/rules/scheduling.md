---
paths:
  - "apps/**/management/**"
  - "apps/**/tasks.py"
  - "apps/notifications/services.py"
  - "config/scheduler.py"
  - "config/asgi.py"
---

# Scheduling and delivery

How scheduled work and outbound email and push run (D-015, D-016). Built in Phase 8.

## The schedule

- `config/scheduler.py` holds the one schedule, in code, with only the standard library: hourly ticks that call idempotent commands. Every job runs at startup too, because a host that restarts daily would otherwise starve a daily job.
- `config/asgi.py` starts it as a task on Daphne's `twisted_loop` when `SCHEDULER_IN_SERVER` is on. That's on by default in prod, off everywhere else, because dev shares its database with prod. `manage.py run_scheduler` runs the same function, once servers share a channel layer. Never run it in two processes.
- Not a daemon thread, which is what this note used to say. `async_to_sync` from a plain thread starts a second loop and touches queues owned by Daphne's, unsafely, and the event then waits for Daphne's next one-second wake-up. Measured on real Daphne over a real socket (2026-11-02, 8 events each): on the loop 170 to 183 ms, mostly the database write, on a thread 459 to 1195 ms. Jobs run through `database_sync_to_async(thread_sensitive=False)`, so `push()` gets back to the right loop, and a slow report can't hold the thread socket logins use.
- `_run` catches everything and logs `Scheduled job <name> failed`. With the database refused, all 4 jobs failed and the server stayed up (2026-11-02). A failed job waits for its next turn: for `generate_reports` that's a day.
- Rejected: a separate process plus a bridge such as Postgres `NOTIFY`, which adds a direct connection and more to break.
- Run jobs at most hourly. Neon's free plan gives 100 CU-hours a month and suspends after 5 idle minutes, so at 0.25 CU, runs every 5 minutes or less keep it awake all month (about 180 CU-hours), while hourly runs use about 18. Tests share that allowance.
- The host must stay on. A sleep or restart skips runs, and each job selects what's due and not yet done, never one time slot, so the next run catches up. Reports can lose a month: see `.claude/rules/reports.md`.
- Hosting must need no card (user, 2026-11-03). Render's free web service fits: 0.1 CPU, 512 MB, 750 hours a month, and the prod server held 118 MB (measured on Windows). It sleeps after 15 minutes with no inbound traffic, so an outside monitor must request `/healthz`, which leaves Neon asleep, about every 10 minutes. A 31-day month is 744 hours, so there's room for only one such service. Set `PORT=10000` on it, because Render's docs don't promise to inject `PORT` into Docker. Its docs neither allow nor forbid a monitor, don't state its proxy count, and say free instances aren't for production and can restart at any time. Checked on vendor pages 2026-11-03.
- `generate_reports` runs daily, because a run costs 2 queries per team already done and 6 per quiet team, so teams get it up to a day after their month ends. It stops at the first AI failure, and the next day carries on.
- `embed_pending` isn't scheduled: searches embed as they go, so it only shortens a backlog. Run it once after the first deploy.

## Reminders

- `send_reminders`, in `apps/tasks/services.py`: open tasks with an active assignee, due within 24 hours or overdue. Assignee only, so unassigned work reaches nobody, and leaders hear nothing about overdue work. A nothing-to-do run costs 2 queries.
- Run-once is `unique_reminder` on recipient, task, kind and `Notification.due_at`, the date the reminder was about. So a moved due date or a new assignee earns a new reminder with no code in `update_task`. `remind()` uses `get_or_create`, so overlapping runs send one.
- No scoping by actor, because a job has no user. The recipient is always the assignee, who can see the task.
- Times are UTC, so a reminder can arrive at night in the team's timezone. Nothing holds it back.

## Delivery

- `notify()` and `remind()` end in `_announce()`: the socket, then `deliver()`. Both channels go over HTTPS with `httpx`, which the project already uses, so there's no SDK. No SMTP, because free hosts block it (Render does).
- `pushed_at` and `emailed_at` are the sent markers, and null means owed. `_send_once` claims with an `update`, so overlapping runs can't both send, then clears the marker on a failure worth retrying: network, 429, 5xx or a garbled reply. A 4xx is final, because both providers say it won't fix itself. Nothing to send still sets the marker.
- `deliver_pending` retries rows under a day old, the life of Resend's `Idempotency-Key`. Past that, a send is dropped, and the row stays in the app. A crash between claim and send loses that send too: at most once, on purpose.
- Sends run inside the request (D-003), at up to 3 seconds each, so an outage can add 6 seconds per recipient. Expo took 0.68 seconds from a dev machine in one probe. Measure on the host. The `shortcut:` comment marks this.
- Comments push but don't email, because of Resend's 100 a day. Addresses ending `.example` are skipped: the seed's can't exist, and a bounce counts against the sender. Email is plain text, so a task title can't inject markup.
- Expo, checked live with a dummy token (2026-11-02): HTTP 200 with a `DeviceNotRegistered` ticket, as handled. Receipts aren't read, so a token that dies later stays until Expo names it in a ticket. Expo says receipts must be checked: see the `shortcut:` comment.
- Resend has never been called for real, because no key exists yet. It needs a `User-Agent`, or it answers a 403 that looks like a bad key. Without a verified domain, it delivers only to the account's owner.
- Tests never reach a provider: `tests/conftest.py` blocks `httpx.post`, and `tests/test_delivery.py` stands in for both.
