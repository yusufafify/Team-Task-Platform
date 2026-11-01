# API Overview

Base path: `/api/v1/`. Requests and responses are JSON only, and every API path ends in a slash. `openapi.yaml` is the full contract; this page covers what a schema can't say.

## Auth

- `POST auth/register/` is open. `POST auth/login/` takes `email` and `password`, and returns `access` and `refresh`.
- Send `Authorization: Bearer <access>` on every other call.
- Access tokens last 15 minutes, refresh tokens 7 days. On a 401, call `POST auth/refresh/` once, then send the user to login if that fails.
- Refresh returns a new `refresh` token as well as `access`, and retires the one you sent. Save the new one straight away.
- Send only one refresh at a time. A second request using the same token gets 401, so queue other calls behind the first.
- Logout: `POST auth/logout/` with `refresh`, which needs no access token, then delete both tokens. On mobile, call `DELETE device-tokens/{token}/` first. An access token keeps working until it expires, up to 15 minutes.
- `POST auth/logout-all/` ends every session of the requester, and takes an access token. Offer it as "sign out everywhere", because it's the way out of a stolen token.
- Token storage: mobile uses `expo-secure-store`. Web keeps the access token in memory and the refresh token in `sessionStorage`, never `localStorage`.
- Limits, answered with 429 and `Retry-After`: login 5 a minute per email and address, 20 a minute per address, 30 a minute per email across all addresses; register 10 an hour per address.

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
| 400 | `{"<field>": ["message"]}`, with `non_field_errors` for problems that aren't about one field |
| 401, 403, 404, 405, 429, 500 | `{"detail": "message"}` |

- 404 also means "not visible to you". Another team's data never answers 403, so clients can't tell whether it exists.
- 403 means the requester can see the thing, but their role can't do that.

## Lists

- Default: `?page=N`, 20 items, with `{count, next, previous, results}`.
- `teams/{id}/messages/`: cursor pages, newest first, with `{next, previous, results}` and no `count`. Follow `next` as given.
- `teams/{id}/members/`: the whole roster as a plain array.
- `GET tasks/` lists every task the requester can see, across teams. Filters: `team`, `status`, `priority`, `assignee`, `overdue=true`. Earliest due first.
- `?overdue=false` and `?unread=false` mean "no filter", not the opposite of the filter.

## Chat and notifications

- There's no WebSocket. To get new messages, poll the first page of `teams/{id}/messages/` and merge by `id`.
- Every authenticated request reads the database, which can suspend only after 5 minutes with no requests at all. Its free compute hours are limited, so these polling rules are required:
  - Poll chat every 10 seconds at most, only while the chat screen is visible.
  - Stop polling after 2 minutes with no user input, and resume on the next input or focus.
  - Don't run any timer while the app is in the background or the tab is hidden.
- `GET notifications/?unread=true` gives the badge count in `count`. Fetch it on app open, on focus and on screen changes, with no timer of its own.
- A notification is created when a task is assigned, and when someone comments on a task you created or are assigned to. Its `title` is a fixed phrase, its `body` is the task's title. Due-soon, overdue, email and push arrive with Phase 3.
- `POST device-tokens/` stores an Expo token. A token already on another account moves to the requester.

## Stats

`GET teams/{id}/stats/?start=YYYY-MM-DD&end=YYYY-MM-DD`

- Dates are whole days in the team's timezone, and `end` is inclusive. `end` defaults to today, and `start` to the first of `end`'s month.
- Leaders get `scope: "team"`, team totals in `stats`, and one row per member in `members`. Members get `scope: "self"`, their own numbers in `stats`, and an empty `members`.
- Rates are fractions from 0 to 1, and null when there's nothing to divide by. `completion_rate` can pass 1, because it compares tasks completed in the period with tasks due in it.
- `overdue` is the count right now, whatever the period. Definitions are in `docs/glossary.md`.

## Health

These sit outside `/api/v1/`, have no trailing slash and need no token.

- `GET /healthz`: the process is up. It doesn't touch the database.
- `GET /readyz`: 200 if the database answers, otherwise 503. It wakes Neon, so use it for deploy checks, not frequent probes.
