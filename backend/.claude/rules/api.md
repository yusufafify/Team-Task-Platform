---
paths:
  - "apps/**/views.py"
  - "apps/**/serializers.py"
  - "apps/**/urls.py"
  - "apps/**/throttles.py"
  - "config/urls.py"
  - "config/views.py"
---

# API

How the Phase 2 API is built, and the choices made without a detailed phase prompt. `docs/decisions.md` is outside this agent's edit list, so they live here. Client-facing rules are in `docs/api/overview.md`.

## Patterns

- Services take the acting user, enforce role and team themselves, and raise DRF exceptions. Phase 5's LLM tools must call these same services, so a check placed only in a view would be skipped.
- A stranger gets 404 from `get_membership`, a member lacking the role gets 403 from `require_leader`. `visible_tasks` is the one scope for tasks and comments.
- Team and assignee ids are plain `IntegerField`s, never related fields, which would reveal which ids exist before the service answers.
- Every view sets `queryset = Model.objects.none()`, so drf-spectacular reads the model without running a user-scoped `get_queryset`.
- Pass `Choices.choices` to a serializer `ChoiceField`, not the class. The class loses the labels and causes an enum collision in the schema.
- An absent `BooleanField` query parameter reads as False, so `false` means "no filter".
- `manage.py spectacular --validate --fail-on-warn` should stay clean.
- Notification failures are swallowed by `robust=True`, and only the logs show them. Keep variable text in `body`, because `title` holds 200 characters.
- Write `completed_at` only when the status changes. A stale instance writing it alongside other edits breaks the database constraint.
- In services, take `get_object_or_404` from `rest_framework.generics` for any id that isn't an `<int:>` path value. Django's raises `ValueError` on a non-numeric id.

## Decisions

- Error format: DRF's default, not RFC 9457. Django's own 400, 404 and 500 pages are replaced by `{"detail": ...}`.
- JSON-only renderers and parsers apply in every environment, so dev matches prod.
- Registration is open, any user can create a team, and leaders add existing accounts by email. Invitations need email, so they wait for Phase 3 at least.
- Members may change only `status`, and other fields are refused with 403, not ignored. Comments and messages can't be edited or deleted.
- Chat transport is REST polling, because the server is WSGI with no broker. Cursor pagination keeps pages stable while messages arrive.
- Tokens stay in the JSON body for both clients. Refresh tokens rotate, and used ones are blacklisted. `auth/logout/` revokes one, and `auth/logout-all/` revokes all of a user's. Any future password change should call `revoke_all_tokens`.
- Stats period: whole days in the team's timezone, defaulting to the month so far. Stats and notifications live in existing apps, so there's no new app.
- In-app notifications exist for assignment and comments. Phase 3 adds due-soon, overdue, email and push.

## Limits

- Login has three limits, in this order: 5/min per account and address, 20/min per address, 30/min per account. `LoginView.check_throttles` stops at the first refusal, because DRF otherwise counts refused requests too, and one address could use up the account's cap.
- Seven or more addresses working together can still block an account's login for up to a minute. Accepted, because dropping the cap would leave distributed guessing unlimited.
- Rotation has no reuse detection. A thief who refreshes first keeps a working chain, and the owner gets a 401 on their next refresh. `auth/logout-all/` ends it.
- A logged-out access token keeps working for up to 15 minutes.
- Throttles use the database cache, so each login costs extra queries. Don't add throttling to read endpoints without measuring.
- Prod requires `DJANGO_NUM_PROXIES`, and it must match the real host, or the address limits can be forged.
- The server can't make polling cheap: JWT auth loads the user from the database on every request, so each one restarts Neon's 5-minute suspend timer. A rate limit wouldn't help, because it hits the database too. The idle-stop rule in `overview.md` is the only control, and it relies on clients following it.
- Registration and `add_member` reveal whether an email has an account. Login doesn't. Accepted for now.
- Not built: password reset or change, email change, leaving a team, date filters on tasks.
