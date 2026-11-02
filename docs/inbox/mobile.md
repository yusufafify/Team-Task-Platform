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

### [BE-003] Browser auth now uses HttpOnly cookies, and mobile has its own endpoints
- From: backend | To: web, mobile | Date: 2026-11-01
- Type: breaking-change
- Details: Replaces all token handling in BE-001 and BE-002, and the polling rules still stand. Web stores nothing: both tokens are `HttpOnly` cookies, so send `credentials: "include"` on every request, and never put a token in browser storage. `POST auth/login/` returns the user, while `auth/refresh/` and `auth/logout/` take no body and return 204. If a refresh gets 401, retry the original call once before going to login, because another tab may have refreshed. Locally, use `localhost` for both the app and the API. Mobile uses `auth/mobile/login/`, `auth/mobile/refresh/` and `auth/mobile/logout/`, keeps tokens only in `expo-secure-store`, and sends `Authorization: Bearer`. Those endpoints refuse any request with an `Origin` header. The rules are in the "Auth" section of `docs/api/overview.md`.
- Status: open
- Resolution:

### [BE-004] Deployment and push now come last
- From: backend | To: web, mobile | Date: 2026-11-01
- Type: notice
- Details: No endpoint changed. The backend roadmap moved deployment and the event pipeline from Phase 3 to Phase 8, the last phase, so this replaces BE-001's "push delivery arrives with Phase 3". Keep registering Expo tokens with `POST device-tokens/`, but nothing is pushed until Phase 8. Due-soon, overdue and email notifications move with it. There is no deployed API until then, so build against a local server. The new order is Phase 3 AI provider layer, Phase 4 chatbot, Phase 5 RAG, Phase 6 monthly AI reports, Phase 7 seed data and final coverage.
- Status: open
- Resolution:

### [BE-005] Errors now carry a stable code, and every response has a request ID
- From: backend | To: web, mobile | Date: 2026-11-02
- Type: notice
- Details: Every `{"detail": ...}` error now also has `code`, for example `{"detail": "Not found.", "code": "not_found"}`, so branch on `code`, never on the text. A 500 also has `request_id`: show it on the error screen. Every response has an `X-Request-ID` header. Field errors on a 400 are unchanged, but unreadable JSON is a 400 with `code: "parse_error"` and no field map. Token errors no longer send `messages`. The full table and the codes are in the "Errors" section of `docs/api/overview.md`.
- Status: open
- Resolution:

### [BE-006] The AI assistant is available
- From: backend | To: web, mobile | Date: 2026-11-02
- Type: notice
- Details: New: `GET`, `POST` and `DELETE teams/{id}/assistant/messages/`. `POST {"question": "..."}` returns 201 with `{question, answer, cached}`. It can take up to 25 seconds, so show a waiting state, set the client's timeout above 30 seconds, block a second send, and never retry on your own. Handle 429 `throttled` with `Retry-After` and 503 `ai_unavailable`, and keep the question in the input box, because a failed one isn't saved. Show `body` as plain text only: never render it as HTML or Markdown, and never auto-load an image or link from it, because answers can repeat text other people wrote. Don't poll the thread. Offer `DELETE` as "New conversation". The rules are in the "Assistant" section of `docs/api/overview.md`.
- Status: open
- Resolution:

### [BE-007] Chat and notifications now arrive on a live socket
- From: backend | To: web, mobile | Date: 2026-11-02
- Type: notice
- Details: Don't poll chat: this replaces the polling rules. Open one socket per signed-in person at `/api/v1/ws/`. Send `Authorization: Bearer <access>` in the third constructor argument, `{headers: {...}}`. The React Native JavaScript passes headers through, but its native layers were not tested, so confirm on a device and write to `docs/inbox/backend.md` if the header does not arrive. It delivers `{"type": "message" | "notification", "data": ...}`, with `data` shaped like REST. Keep sending with `POST`. After every connect, fetch the first page of messages and the unread count, then merge by `id`, because the socket can miss events and can repeat them. Close code `4401` means refresh and reconnect. On any other drop, reconnect with backoff from 1 to 30 seconds. The full rules are under "Live socket" in `docs/api/overview.md`.
- Status: open
- Resolution:

### [BE-008] Poll only as a fallback while the socket is down
- From: backend | To: web, mobile | Date: 2026-11-02
- Type: notice
- Details: This corrects BE-007, which said not to poll at all. Keep the socket as the main path, and never poll while it's up. If 3 reconnects in a row fail, the network may be blocking sockets, so fetch the first page of messages for the open chat and the unread count at most every 10 seconds, only while that screen is visible. Stop after 2 minutes with no input, run no timer in the background, keep trying to reconnect, and stop polling once the socket connects. The rules are under "Live socket" in `docs/api/overview.md`. No endpoint changed.
- Status: open
- Resolution:

### [BE-009] Monthly AI reports are available to leaders
- From: backend | To: web, mobile | Date: 2026-11-02
- Type: notice
- Details: New: `GET teams/{id}/reports/`, read-only, default pages, newest month first. Each result is `{id, month, stats, members, body, created_at}`. Leaders only: a member gets 403 and a stranger 404, so hide the screen from members. `stats` has the same fields as `GET teams/{id}/stats/`, and each `members` row is `{name, stats}`. These numbers are frozen when the report is written, so they can differ from live stats later. Show `body` as plain text with its line breaks: never render it as HTML or Markdown, and never auto-load an image or link from it. A quiet month has no report, so show an empty state. No notification is sent yet, so fetch on opening the screen and don't poll. The rules are in the "Reports" section of `docs/api/overview.md`. No existing endpoint changed.
- Status: open
- Resolution:
