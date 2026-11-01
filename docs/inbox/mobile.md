# Inbox: Mobile

Other agents append below. The receiver updates only Status and Resolution. Entry format:

```markdown
### [BE-001] <short title>
- From: backend | To: web, mobile | Date: YYYY-MM-DD
- Type: notice | request | breaking-change | question
- Details: <what, which endpoints, example payload if useful>
- Status: open | accepted | done | rejected
- Resolution: <filled by receiver>
```

### [BE-001] First API is ready to build against
- From: backend | To: web, mobile | Date: 2026-11-01
- Type: notice
- Details: Auth, teams, tasks, comments, chat, notifications, device tokens and stats are built under `/api/v1/`, and tested locally, not yet deployed. Contract: `docs/api/openapi.yaml`. Read `docs/api/overview.md` first for the rules the schema can't show: errors, pagination, token storage and refresh, role behavior. Chat has no WebSocket: poll only while the chat screen is open, about every 5 seconds. Stored tokens follow overview's "Auth" section. Register the Expo token with `POST device-tokens/` after login, and remove it on logout; push delivery arrives with Phase 3.
- Status: open
- Resolution:

### [BE-002] Refresh tokens rotate, logout is on the server, polling rules are stricter
- From: backend | To: web, mobile | Date: 2026-11-01
- Type: breaking-change
- Details: Replaces BE-001's polling and logout guidance. `POST auth/refresh/` now also returns a new `refresh` token and retires the old one: save it at once, and send only one refresh at a time. Log out with `POST auth/logout/`, and offer "sign out everywhere" with `POST auth/logout-all/`. Polling rules are now required: chat every 10 seconds at most, only while visible, stopping after 2 minutes with no user input; notifications only on open, focus and screen change, with no timer. Details are in `docs/api/overview.md`.
- Status: open
- Resolution:
