---
paths:
  - "apps/**/views.py"
  - "apps/**/throttles.py"
  - "config/urls.py"
  - "config/views.py"
---

# API Limits

What the API can't do yet, and the limits accepted on purpose.

- Login has three limits, in this order: 5/min per account and address, 20/min per address, 30/min per account. `LoginView.check_throttles` stops at the first refusal, because DRF otherwise counts refused requests too, and one address could use up the account's cap.
- Seven or more addresses working together can still block an account's login for up to a minute. Accepted, because dropping the cap would leave distributed guessing unlimited.
- Rotation has no reuse detection. A thief who refreshes first keeps a working chain, and the owner gets a 401 on their next refresh. `auth/logout-all/` ends it.
- A logged-out access token keeps working for up to 15 minutes.
- Throttles use the database cache, so each login costs extra queries. Don't add throttling to read endpoints without measuring.
- Prod requires `DJANGO_NUM_PROXIES`, and it must match the real host, or the address limits can be forged.
- Cookies need the web app and API on one site. A host's shared domain, such as `vercel.app`, usually counts as separate sites, and the project has no budget for a domain, so prod uses a free same-origin proxy: the web host forwards `/api/*` to the API. The proxy counts toward `DJANGO_NUM_PROXIES`, and the web origin must be in `CORS_ALLOWED_ORIGINS`.
- The server can't make polling cheap: JWT auth loads the user from the database on every request, so each one restarts Neon's 5-minute suspend timer. A rate limit wouldn't help, because it hits the database too. That's why clients use the socket, which touches the database only on connect.
- The socket's channels are in memory, so it needs exactly one server process. So the scheduler runs inside the server for now: see `.claude/rules/scheduling.md`. The steps past one process are in `README.md`. `push()` must stay the only sender, and event data must stay msgpack-safe, which `tests/test_realtime.py` checks, or that swap stops being a settings change. It has never been run on a real shared layer.
- Cookies must reach the socket, so the web host's `/api/*` proxy has to forward WebSocket upgrades. Check this before choosing a host. If it can't, web runs on the polling fallback, and live updates need a short-lived ticket endpoint, which isn't built.
- Not limited: sockets per person. A socket can miss an event if its queue passes the layer's 100, which is why clients catch up through REST.
- Registration and `add_member` reveal whether an email has an account. Login doesn't. Accepted for now.
- Not built: password reset or change, email change, leaving a team, date filters on tasks.
