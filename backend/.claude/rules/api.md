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

- Services take the acting user, enforce role and team themselves, and raise DRF exceptions. Phase 4's LLM tools must call these same services, so a check placed only in a view would be skipped.
- A stranger gets 404 from `get_membership`, a member lacking the role gets 403 from `require_leader`. `visible_tasks` is the one scope for tasks and comments.
- Team and assignee ids are plain `IntegerField`s, never related fields, which would reveal which ids exist before the service answers.
- Every view sets `queryset = Model.objects.none()`, so drf-spectacular reads the model without running a user-scoped `get_queryset`.
- Pass `Choices.choices` to a serializer `ChoiceField`, not the class. The class loses the labels and causes an enum collision in the schema.
- An absent `BooleanField` query parameter reads as False, so `false` means "no filter".
- `manage.py spectacular --validate --fail-on-warn` should stay clean.
- Notification failures are swallowed by `robust=True`, and only the logs show them. Keep variable text in `body`, because `title` holds 200 characters.
- Write `completed_at` only when the status changes. A stale instance writing it alongside other edits breaks the database constraint.
- In services, take `get_object_or_404` from `rest_framework.generics` for any id that isn't an `<int:>` path value. Django's raises `ValueError` on a non-numeric id.
- Setting `permission_classes` on a view replaces the defaults, so it can make a view public by accident. `tests/test_api_platform.py` walks every URL and requires a 401 unless the route is in `PUBLIC_ROUTES`, so a new public route must join that list on purpose.

## Decisions

- Error format: `{"detail", "code"}` from `config/exceptions.py`, and a map of fields for invalid input, not RFC 9457: two first-party clients gain nothing from its media type. Django's own 400, 404 and 500 pages use the same shape, and a 500 adds `request_id`.
- `config/exceptions.py` also turns Django's `ValidationError` into a 400. DRF's handler skips it, so a crafted cursor answered 500 (found 2026-11-02).
- Auth has no middleware. `DEFAULT_PERMISSION_CLASSES` keeps every view private unless it opts out, and middleware would run before DRF's auth and need its own list of public routes. The one project middleware is `config/request_id.py`. It runs first, ignores any ID a client sends, and never resets the ID, because Django logs 4xx and 5xx responses after the middleware returns.
- JSON-only renderers and parsers apply in every environment, so dev matches prod.
- Registration is open, any user can create a team, and leaders add existing accounts by email. Invitations need email, so they wait for Phase 8 at least.
- Members may change only `status`, and other fields are refused with 403, not ignored. Comments and messages can't be edited or deleted.
- Live events: one push-only WebSocket per person at `/api/v1/ws/`, on Channels and Daphne (user's decision, 2026-11-02). `apps/notifications/consumers.py` is the consumer, and `push()` in its services is the only sender. REST stays the source of truth, and writes stay on REST, so permissions aren't duplicated.
- One group per user, with no team groups: a message reads the team's members when sent, so removal takes effect at once with no unsubscribe code. It costs one query per message.
- Socket auth: Bearer from any origin, because a page script can't set that header. A cookie counts only with an `Origin` in `CORS_ALLOWED_ORIGINS`, because browsers attach cookies by themselves. React Native may send its own `Origin`, so don't apply the check to Bearer.
- A socket outlives its token, so `deliver` checks expiry and closes with 4401, and no timer is needed. Daphne pings every 20 seconds and drops silent clients after 30, so no heartbeat code exists.
- Web: both tokens sit in `HttpOnly`, `SameSite=Strict` cookies and never appear in a body, by the user's decision.
- Mobile: `auth/mobile/*` returns tokens in the body for `expo-secure-store`, sent as Bearer. The user chose this because a phone must hold the session somewhere, the React Native docs call cookie auth unstable, and `HttpOnly` guards against XSS, which native apps don't have.
- CSRF: `TrustedOrigin` replaces Django's CSRF tokens, so clients hold nothing. It's a default permission, so any view setting `permission_classes` must include it or `NoBrowser`.
- `NoBrowser` keeps page scripts off the mobile endpoints. Mobile refresh reads only the body, so a cookie can never be turned into a token in a response.
- Refresh tokens rotate, and used ones are blacklisted. `auth/logout-all/` revokes all of a user's, on both clients. Any future password change should call `revoke_all_tokens`.
- A failed web refresh leaves cookies alone. Cookies are shared across tabs, so a second tab can lose the race, and clearing them would end the first tab's new session.
- Stats period: whole days in the team's timezone, defaulting to the month so far. Stats and notifications live in existing apps, so there's no new app.
- Notification kinds and who gets them are in `docs/api/overview.md`. Reminders, email and push are in `.claude/rules/scheduling.md`.
