# API Overview

Base path: `/api/v1/`. Requests and responses are JSON only, and every API path ends in a slash. `openapi.yaml` is the full contract; this page covers what a schema can't say.

## Auth

Web and mobile authenticate differently. `POST auth/register/` is the same for both, and is open. Access tokens last 15 minutes, refresh tokens 7 days, and each refresh retires the token it used.

### Web, and any other browser client

Both tokens live in `HttpOnly` cookies. JavaScript can't read them, and the web app stores nothing. Never put a token in any browser storage.

- Send every request with `credentials: "include"`.
- `POST auth/login/` takes `email` and `password`, sets the cookies and returns the user.
- To check whether someone is logged in, call `GET auth/me/`, which answers 200 or 401.
- On a 401, call `POST auth/refresh/` with no body, then retry the original call.
- If that refresh also gets 401, retry the original call once more, because another tab may have just refreshed. If it still fails, go to login.
- Run only one refresh at a time in each tab, and queue other calls behind it.
- `POST auth/logout/` takes no body, and clears the cookies.
- In prod, the web host proxies `/api/*` to the API, so call relative `/api/...` paths from the same domain as the app. Cookies won't work if the app calls the API's own domain directly. Locally, use `localhost` for both, not `127.0.0.1`.
- Writes from an origin the API doesn't know get 403.

### Mobile

There are no cookies here. The app keeps both tokens, in the device's encrypted storage only.

- `POST auth/mobile/login/` takes `email` and `password`, and returns `access` and `refresh`.
- Store both only in `expo-secure-store`. Never use AsyncStorage, and never log them.
- Send `Authorization: Bearer <access>` on every other call.
- On a 401, call `POST auth/mobile/refresh/` with `refresh`. It returns a new `access` and `refresh`, so save both straight away.
- Run only one refresh at a time, and queue other calls behind it. A second request using the same token gets 401.
- To log out, call `DELETE device-tokens/{token}/`, then `POST auth/mobile/logout/` with `refresh`, then delete both tokens.
- These three endpoints refuse any request with an `Origin` header. Native requests shouldn't send one, so a 403 here means something added it.

### Both

- `POST auth/logout-all/` ends every session of the requester, on every device. Offer it as "sign out everywhere", because it's the way out of a stolen token.
- A logged-out access token keeps working until it expires, up to 15 minutes.
- Limits, answered with 429 and `Retry-After`: login 5 a minute per email and address, 20 a minute per address, 30 a minute per email across all addresses; register 10 an hour per address. Web and mobile logins share these limits.

## Teams and roles

- Anyone with an account can create a team, and becomes its leader. Leaders add people by the email of an existing account; there are no invitations yet.
- The role belongs to the membership, so one user can lead one team and be a member of another. Each team in `GET teams/` carries the requester's `role`.
- A team always keeps at least one leader. Only a team with no tasks or messages can be deleted.
- Removing a member unassigns their unfinished tasks. Finished tasks keep the assignee for history.
- Leaders see and edit everything in their team. Members see only tasks assigned to them, and can change only `status`.
- Sending any other field as a member returns 403, and nothing is saved.

## Errors

| Status | Body |
|---|---|
| 400, invalid fields | `{"<field>": ["message"]}`, with `non_field_errors` for problems that aren't about one field |
| 400, unreadable JSON | `{"detail": "message", "code": "parse_error"}` |
| 401, 403, 404, 405, 406, 415, 429, 503 | `{"detail": "message", "code": "<code>"}` |
| 500 | `{"detail": "message", "code": "server_error", "request_id": "<id>"}` |

- Branch on `code`, never on `detail`, which is written for people and may change.
- 401 codes: `not_authenticated` (no token), `token_not_valid` (expired or bad), `no_active_account` (wrong email or password), `user_inactive` (the account was deactivated).
- Other codes: `permission_denied`, `not_found`, `method_not_allowed`, `throttled` (wait for `Retry-After`), `ai_unavailable` (the assistant is down, so try later).
- Every response carries an `X-Request-ID` header, and a 500 repeats it as `request_id`. Show that ID on an error screen, because it's how a report is matched to the server's logs.
- 404 also means "not visible to you". Another team's data never answers 403, so clients can't tell whether it exists.
- 403 means the requester can see the thing, but their role can't do that.

## Lists

- Default: `?page=N`, 20 items, with `{count, next, previous, results}`.
- `teams/{id}/messages/`: cursor pages, newest first, with `{next, previous, results}` and no `count`. Follow `next` as given.
- `teams/{id}/members/`: the whole roster as a plain array.
- `GET tasks/` lists every task the requester can see, across teams. Filters: `team`, `status`, `priority`, `assignee`, `overdue=true`. Earliest due first.
- `?overdue=false` and `?unread=false` mean "no filter", not the opposite of the filter.

## Chat and notifications

- New messages and notifications arrive on the live socket below. Poll only as the fallback described there, because every request reads the database, whose free compute hours are limited.
- `GET notifications/?unread=true` gives the badge count in `count`. Fetch it on app open, on focus and on screen changes, with no timer of its own.
- `kind` says what happened, and its `title` is a fixed phrase:

| `kind` | Sent when | `body` | Email |
|---|---|---|---|
| `task_assigned` | A task is assigned to you | The task's title | Yes |
| `task_commented` | Someone comments on a task you created or are assigned to | The task's title | No |
| `task_due_soon` | Your open task is due within 24 hours | The task's title | Yes |
| `task_overdue` | Your open task has passed its due date | The task's title | Yes |
| `report_ready` | A monthly report is written, for the team's leaders | `<team name>: <month>` | Yes |

- Reminders come from a job that runs about once an hour, so a `task_due_soon` can arrive up to an hour after the 24-hour mark. You get one of each per due date, so moving a due date can bring another.
- A `report_ready` has `task: null` and no team id, so open the reports screen, and read the team's name from `body`.
- Every kind also goes to the recipient's phones as a push, sent by the server. Socket events and pushes are separate, so a phone in the foreground can get both.
- A push carries the notification's `title` and `body`, plus `data`: `{"notification": 9, "kind": "task_assigned", "task": 4}`. `task` can be null. Use `data` to open the right screen when someone taps it.
- A failed push or email is retried about hourly for a day, then dropped. The notification itself stays in `GET notifications/`, so show that list as the record, and treat email and push as a nudge.

### Live socket

Open one WebSocket per signed-in person, at `/api/v1/ws/`. It covers all of that person's teams, so there's nothing to subscribe to. It only delivers: keep sending messages with `POST`, and anything a client sends on the socket is ignored.

- Web: `new WebSocket()` on the same domain as the app, using `wss:` in prod. The login cookie goes with it, and the page's origin must be an allowed one.
- Mobile: send `Authorization: Bearer <access>` in the constructor's third argument, `{headers: {...}}`.

Each event is JSON with a `type` and `data`, and `data` has the same shape as the REST API returns:

```json
{"type": "message", "data": {"id": 7, "team": 1, "author": {"id": 2, "email": "...", "first_name": "...", "last_name": "..."}, "body": "Hello", "created_at": "..."}}
{"type": "notification", "data": {"id": 9, "kind": "task_commented", "title": "...", "body": "...", "task": 4, "read_at": null, "created_at": "..."}}
```

- The socket can miss events, and the server keeps nothing for it, so REST stays the source of truth. After every connect, fetch the first page of `teams/{id}/messages/` for the open chat and the unread count, then merge by `id`. The same event can arrive twice, including your own message after you post it.
- Close code `4401` means the token is missing or expired. Call refresh, then reconnect. It also arrives on a connected socket: a token isn't checked again until the next event, so a socket can stay open and quiet after its token expires. Closing is how you learn, and the fetch after reconnecting recovers that event.
- Any other drop means reconnect: wait 1 second, double it each try up to 30, and add up to 20% random jitter.
- If 3 reconnects in a row fail, the network may be blocking sockets, so poll as a fallback and keep trying to reconnect:
  - Fetch the first page of `teams/{id}/messages/` for the open chat and the unread count, at most every 10 seconds, only while that screen is visible.
  - Stop after 2 minutes with no user input, and resume on the next input or focus.
  - Don't run any timer while the app is in the background or the tab is hidden.
  - Stop polling as soon as the socket connects. Never poll while it's up.
- On mobile, close the socket when the app goes to the background and reconnect on return. On web, reconnect when a hidden tab comes back if the socket has dropped.
- Show when the socket is down, because new messages will be slow to appear until it's back.
- Someone removed from a team stops getting its events at once. Their socket stays open for their other teams.
- `POST device-tokens/` stores an Expo token. A token already on another account moves to the requester. The server deletes a token Expo says is dead, so register again after every login, and whenever the app gets a new one.

## Assistant

An AI assistant answers questions about the team's work, using only what the person asking is allowed to see. It reads and never changes anything, so it can't create or edit a task.

- `teams/{id}/assistant/messages/`: `POST` asks, `GET` lists, `DELETE` clears.
- Each person has one private thread per team. Not even a leader can read a member's thread.
- `POST` takes `{"question": "..."}`, up to 2000 characters, and returns 201 with `{question, answer, cached}`. `question` and `answer` are saved messages, and `cached: true` means the answer was reused, so no AI request was spent.
- A question can take up to 25 seconds, so show a waiting state, set the client's timeout above 30 seconds, and block a second send until the first returns. Don't retry on your own, because each try spends scarce AI requests.
- On 429 (`throttled`), wait for `Retry-After`, which can be hours when the day's limit is used up. On 503 (`ai_unavailable`), let the user try again later. A failed question isn't saved, so keep its text in the input box.
- Show `body` as plain text. Never render it as HTML or Markdown, and never load an image or open a link from it automatically. Answers can repeat text other people wrote in tasks and comments.
- `GET` uses cursor pages, newest first, like chat: `{next, previous, results}`, with no `count`. A thread changes only when its owner asks a question, so never poll it.
- `DELETE` returns 204 and clears the requester's thread only. Offer it as "New conversation".
- The assistant remembers the last hour of a thread. Older messages stay readable, but it no longer sees them, so a follow-up after a long gap may need rephrasing.
- A thread is deleted when its owner leaves the team, or stops being a leader.

## Stats

`GET teams/{id}/stats/?start=YYYY-MM-DD&end=YYYY-MM-DD`

- Dates are whole days in the team's timezone, and `end` is inclusive. `end` defaults to today, and `start` to the first of `end`'s month.
- Leaders get `scope: "team"`, team totals in `stats`, and one row per member in `members`. Members get `scope: "self"`, their own numbers in `stats`, and an empty `members`.
- Rates are fractions from 0 to 1, and null when there's nothing to divide by. `completion_rate` can pass 1, because it compares tasks completed in the period with tasks due in it.
- `overdue` is the count right now, whatever the period. Definitions are in `docs/glossary.md`.

## Reports

A monthly report sums up one team's month: numbers worked out by the server, and a short summary written by the AI.

`GET teams/{id}/reports/`

- Leaders only, because a report rates every member. A member gets 403, and a stranger 404. Hide the screen from members.
- Default pages, newest month first. `month` is the first day of the month, in the team's timezone.
- `stats` and `members` hold the same numbers as `GET teams/{id}/stats/` for that month, but frozen when the report was written. So they can differ from live stats later, and that's correct. `overdue` is the count on the day of writing. A member row has `name` in place of `user`, and someone who had left the team by then has no row.
- Show `body` as plain text with its line breaks. Never render it as HTML or Markdown, and never load an image or open a link from it automatically, because it can repeat text other people wrote. It normally has the headings Summary, Achievements, Risks and Next month, but the AI writes them, so don't parse it.
- Clients can't create, change or delete a report. The server writes one within a day of each month ending, on a schedule. A month with no activity gets none, so show an empty state.
- A new report sends leaders a `report_ready` notification. Fetch the list when the screen opens or when that arrives, and never poll it.

## Health

These sit outside `/api/v1/`, have no trailing slash and need no token.

- `GET /healthz`: the process is up. It doesn't touch the database.
- `GET /readyz`: 200 if the database answers, otherwise 503. It wakes Neon, so use it for deploy checks, not frequent probes.
