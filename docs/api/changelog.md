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
