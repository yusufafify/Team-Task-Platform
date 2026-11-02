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
- The server can't make polling cheap: JWT auth loads the user from the database on every request, so each one restarts Neon's 5-minute suspend timer. A rate limit wouldn't help, because it hits the database too. The idle-stop rule in `overview.md` is the only control, and it relies on clients following it.
- Registration and `add_member` reveal whether an email has an account. Login doesn't. Accepted for now.
- Not built: password reset or change, email change, leaving a team, date filters on tasks.
