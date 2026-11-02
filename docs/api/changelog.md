# API Changelog

Newest entries go at the bottom. Entry format:

```markdown
## YYYY-MM-DD — <endpoint(s)>
- Change: added | changed | removed | deprecated
- Breaking: yes/no
- Notes: <one or two lines>
```

## 2026-11-01 — all of `/api/v1/`, `/healthz`, `/readyz`
- Change: added
- Breaking: no
- Notes: First API: auth, teams and members, tasks, comments, chat, notifications, device tokens and stats. Error format, pagination and polling rules are in `overview.md`.

## 2026-11-01 — `POST /api/v1/auth/refresh/`
- Change: changed
- Breaking: yes
- Notes: The response now includes a new `refresh` token, and the one sent is retired. No client exists yet.

## 2026-11-01 — `POST /api/v1/auth/logout/`, `POST /api/v1/auth/logout-all/`
- Change: added
- Breaking: no
- Notes: Server-side revocation of one refresh token, or of all a user's refresh tokens.

## 2026-11-01 — `POST /api/v1/auth/login/`
- Change: changed
- Breaking: no
- Notes: The 5-a-minute limit is now per email and address, with a new 30-a-minute limit per email across addresses.

## 2026-11-01 — `POST /api/v1/auth/login/`, `/refresh/`, `/logout/`
- Change: changed
- Breaking: yes
- Notes: Browser auth moved to `HttpOnly` cookies. Login returns the user and sets cookies, refresh and logout take no body and return 204, and no token appears in any body. No client exists yet.

## 2026-11-01 — `POST /api/v1/auth/mobile/login/`, `/mobile/refresh/`, `/mobile/logout/`
- Change: added
- Breaking: no
- Notes: The mobile app's token flow, sent as Bearer. Requests with an `Origin` header get 403.

## 2026-11-01 — all write endpoints
- Change: changed
- Breaking: no
- Notes: A write from an origin outside the allowed list gets 403.

## 2026-11-02 — every endpoint
- Change: changed
- Breaking: no
- Notes: Errors with a `detail` now also carry a stable `code`, a 500 adds `request_id`, and every response has an `X-Request-ID` header. Token errors lose their undocumented `messages` key. A crafted chat `cursor` now gets 400, not 500. No client exists yet.
