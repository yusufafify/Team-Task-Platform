import time
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.exceptions import APIException, Throttled

from apps.teams.models import Team

from . import provider
from .models import AICall

User = get_user_model()
# Gemini's daily quota resets at midnight Pacific, so the daily counts must too.
QUOTA_TIMEZONE = ZoneInfo("America/Los_Angeles")
RESERVE_LOCK = 3001  # Any number, as long as no other advisory lock in this database uses it.


class AIUnavailable(APIException):
    status_code = 503
    default_detail = "The assistant is unavailable right now. Try again later."
    default_code = "ai_unavailable"


def generate(
    feature: AICall.Feature,
    prompt: str | list[dict],
    *,
    user: User | None = None,
    team: Team | None = None,
    system: str | None = None,
    tools: list[dict] | None = None,
) -> provider.Reply:
    """The one way to reach the LLM. Pass `user=None` for work no person asked for.

    Never call this inside `transaction.atomic`: the lock would be held for the whole request,
    and a rollback would erase the log row, so the request would go uncounted.
    """
    call = _reserve(feature, user, team)
    started = time.monotonic()
    try:
        reply = provider.send(prompt, system=system, tools=tools)
    except provider.ProviderError as exc:
        _finish(call, started, AICall.Status.FAILED, error=str(exc))
        if isinstance(exc, provider.QuotaExceeded):
            raise Throttled() from exc
        raise AIUnavailable() from exc
    if reply.status not in ("completed", "requires_action"):
        _finish(call, started, AICall.Status.FAILED, reply, f"Provider status: {reply.status}")
        raise AIUnavailable()
    _finish(call, started, AICall.Status.SUCCEEDED, reply)
    return reply


def _reserve(feature: AICall.Feature, user: User | None, team: Team | None) -> AICall:
    """Log the call before sending it, so failures and crashes still count against the limits."""
    with transaction.atomic():
        # Counting and inserting must be one step, or concurrent calls all take the last slot.
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [RESERVE_LOCK])
        now = timezone.now()
        minute_ago = now - timedelta(minutes=1)
        day_start = now.astimezone(QUOTA_TIMEZONE).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        counts = AICall.objects.filter(created_at__gte=min(minute_ago, day_start)).aggregate(
            minute=Count("pk", filter=Q(created_at__gte=minute_ago)),
            day=Count("pk", filter=Q(created_at__gte=day_start)),
            user_day=Count("pk", filter=Q(created_at__gte=day_start, user=user)),
        )
        over_user_limit = user and counts["user_day"] >= settings.AI_REQUESTS_PER_USER_PER_DAY
        # Daily limits first, so a caller over both is told the longer wait.
        if over_user_limit or counts["day"] >= settings.AI_REQUESTS_PER_DAY:
            # `now` is in UTC here, so this subtraction stays right across a clock change.
            raise Throttled(wait=(day_start + timedelta(days=1) - now).total_seconds())
        if counts["minute"] >= settings.AI_REQUESTS_PER_MINUTE:
            raise Throttled(wait=60)
        return AICall.objects.create(feature=feature, model=settings.AI_MODEL, user=user, team=team)


def _finish(
    call: AICall,
    started: float,
    status: AICall.Status,
    reply: provider.Reply | None = None,
    error: str = "",
) -> None:
    call.status = status
    call.error = error[:500]
    call.latency_ms = round((time.monotonic() - started) * 1000)
    if reply:
        call.input_tokens = reply.input_tokens
        call.output_tokens = reply.output_tokens
        call.total_tokens = reply.total_tokens
    call.save()
