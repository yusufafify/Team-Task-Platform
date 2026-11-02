# Backend Handover

Hard cap about 80 lines.

## Current state

- Date: 2026-11-02
- Roadmap phase: Phases 1 to 7 are ticked, with CI deferred. Phase 8 is half done: the event pipeline is built, the deploy isn't.
- Repository: `yusufafify/Team-Task-Platform`, working branch `backend`. Only the user commits.

## Done this session

- Built Phase 8's code from the roadmap line, with no detailed prompt. Design is in `.claude/rules/scheduling.md`.
- `send_reminders`, `deliver_pending`, `run_scheduler`, `config/scheduler.py`, Expo push and Resend email over `httpx`, `report_ready` notifications, migration `notifications/0002`, `Dockerfile` and `.dockerignore`. `gunicorn` is removed.
- Changed the plan: the scheduler runs on Daphne's loop, not in a daemon thread, because measured latency and thread safety both ruled the thread out.
- Published as BE-010, with a changelog entry and `openapi.yaml`. The README now has rollback and smoke steps, which closes that audit item.
- My decisions, not asked: comments push but don't email; reminders go to the assignee only; a failed send retries hourly for a day; `RESEND_API_KEY` is required in prod; generate_reports runs daily; no SDKs.

## Verification

- Full suite on the final code: 659 passed in 18 minutes. Ruff, `ruff format --check`, `makemigrations --check` and `spectacular --validate --fail-on-warn` are clean.
- 27 of 27 deliberate breaks caught, each removing one safeguard. Files restored and checked afterwards.
- Real Daphne, real socket, `test_neondb`: a scheduled reminder reached the socket in 170 to 183 ms. The plain-thread plan took 459 to 1195 ms.
- Image steps rehearsed by hand in a clean copy with no `.env`: `collectstatic`, `check --deploy` (clean, and the first time it ran), and prod Daphne. HTTPS redirect, forged host and `/healthz` were right. With the database refused, 4 jobs failed and the server stayed up.
- Real Expo called once with a dummy token: HTTP 200 and a `DeviceNotRegistered` ticket, as handled, in 0.68 seconds.
- Never tested: the Docker image itself, Resend for real, a real phone or browser, Daphne on Linux, and a real proxy's `DJANGO_NUM_PROXIES`.

## Earlier work, still true

- Phases 3 to 6 and the socket were checked live. Details are in `.claude/rules/ai.md`, `assistant.md`, `retrieval.md`, `reports.md` and `api.md`.
- `main` has 5 users, the Demo Team of 4, 15 tasks, 7 comments and 7 messages, 16 `Embedding` rows and 1 `MonthlyReport`. 13 of the 29 tasks, comments and messages have no `Embedding` row yet.

## In progress

Phase 8's deploy, waiting on the user. They have no card or billing details to give and no Docker on this machine (2026-11-03), so every card-based host is out, and the host builds the image. Recommended: Render's free web service with an outside monitor on `/healthz`. Back4app is the backup. Details are in `.claude/rules/scheduling.md`.

## Next steps

1. The user signs up on Render with no card, and commits and pushes this work, because Render builds from the repo.
2. The user creates a Resend key, which prod needs to start. Set the variables in README's table, deploy, run its "Check it's working" list, then `embed_pending` once, then tick Phase 8.
3. Keeping the web app same-origin: serving its build from this container avoids needing a proxy that forwards WebSocket upgrades. Vercel's rewrites aren't confirmed to, and Cloudflare Workers reportedly do. Decide this when `web/` exists, and count whatever proxy remains in `DJANGO_NUM_PROXIES`.
4. Check `SECURE_PROXY_SSL_HEADER` on the real host, and measure a write that sends: sends run inside the request.
5. When the user clears the billing lock, run the Backend workflow, because Phases 1 to 3 have never run in CI.
6. Mobile must confirm on a device that `Authorization` reaches the socket, and that a push arrives.

## Blockers / waiting on other agents

- GitHub Actions won't start jobs: "your account is locked due to a billing issue". The user has deferred fixing this. CI on Linux stays unproven until then. It no longer affects product features (D-015).
- Any further `migrate` or data change on `main` needs the user's approval: `main` serves local work and prod.
- `docs/` reads may need `/add-dir D:\work\Nesma-Airlines\docs` at session start. `.claude/settings.json` lists the folder, but reads were refused until that command ran.
- Agents can't read or edit `.env`.
- Audit items still open, none started: dependency scan in CI, and removing boilerplate docstrings.
- Hosts, from the vendors' pages on 2026-11-02. Northflank's free Sandbox says "Always on, no sleeping" with `code.run` TLS, but its docs require a payment method and say it shouldn't be used for production, and its pricing page shows a security incident banner asking users to rotate credentials. WebSockets aren't stated. Google's e2-micro is always free in 3 US regions with 1 GB RAM and 1 GB egress a month, and needs a billing account, and you run the VM and HTTPS yourself. Oracle's Always Free VMs may be reclaimed when idle for 7 days, which a quiet app is. Render's free tier sleeps, and Koyeb's scales to zero.
- Without a verified domain, email reaches only the Resend account's owner. The project has no domain budget.

## Inbox processed up to

None: the inbox was empty on 2026-11-02.

## History

- 2026-11-02: Phase 6 monthly reports built, migrated, first report written, checked live and ticked.
- 2026-11-02: Phase 7 seed and final coverage built, applied to `main`, report rewritten, checked by hand and ticked.
- 2026-11-03: Phase 8 event pipeline and scheduler built, checked on a real server against the test branch, and `notifications/0002` applied to `main` with the user's approval. Not deployed.
