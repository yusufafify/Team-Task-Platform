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
