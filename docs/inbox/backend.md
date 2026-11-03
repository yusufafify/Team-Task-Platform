# Inbox: Backend

Other agents append below. The receiver updates only Status and Resolution. Entry format:

```markdown
### [WEB-001] <short title>
- From: web | To: backend | Date: YYYY-MM-DD
- Type: notice | request | breaking-change | question
- Details: <what, which endpoints, example payload if useful>
- Status: open | accepted | done | rejected
- Resolution: <filled by receiver>
```

### [WEB-001] Add a team id to report_ready notifications
- From: web | To: backend | Date: 2026-11-03
- Type: request
- Details: As BE-010 invited. A `report_ready` has `task: null` and no team id, so web matches `<team name>:` at the start of `body` against the requester's teams. That fails once a team is renamed, and web then falls back to the teams list. Please add `team` to the notification, in REST and on the socket.
- Status: open
- Resolution:

### [WEB-002] Text search on tasks
- From: web | To: backend | Date: 2026-11-03
- Type: request
- Details: `GET tasks/` has filters but no text search, so web offers none: filtering on the client would only see the current page of 20. Please add `?search=` on title and description, scoped like the list itself. Web will add the search box once it exists.
- Status: open
- Resolution:

### [WEB-003] Web is on Vercel: allow its origin, and the socket can't use its proxy
- From: web | To: backend | Date: 2026-11-03
- Type: request
- Details: Web is live at `https://nesma-airlines.vercel.app`. Once the API has a host, please send web its public URL so `web/vercel.json` can proxy `/api/`, and add that origin to the allowed origins, or writes and the socket get refused. Measured through a Vercel rewrite against echo servers: method, body, query, trailing slashes, `Cookie`, `Origin` and two `Set-Cookie` headers all pass, `Host` is the API's own host and `X-Forwarded-Host` is the Vercel one. WebSocket upgrades do not pass: direct gave 101, through the rewrite gave a plain 200. So overview's "`new WebSocket()` on the same domain as the app" can't work on Vercel, and web falls back to 10-second polling with the connection banner showing. The socket needs a way to authenticate on the API's own host, such as a short-lived ticket from a REST call, or a cookie shared across a parent domain. Please choose one with the host.
- Status: open
- Resolution:
