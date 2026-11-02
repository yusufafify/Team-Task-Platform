import logging
from collections.abc import Callable, Iterable
from datetime import timedelta

import httpx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from rest_framework.generics import get_object_or_404

from apps.notifications.models import DeviceToken, Notification
from apps.notifications.serializers import NotificationSerializer
from apps.tasks.models import Task

User = get_user_model()
logger = logging.getLogger(__name__)

EXPO_URL = "https://exp.host/--/api/v2/push/send"
RESEND_URL = "https://api.resend.com/emails"
# Resend answers 403 without one, which reads like a bad key.
HEADERS = {"User-Agent": "team-task-platform/1.0"}
# shortcut: sends run inside the request, so an outage adds this per send, move off it if it hurts.
TIMEOUT_SECONDS = 3.0
# As long as Resend remembers an idempotency key, so a retry can never send a second email.
RETRY_WINDOW = timedelta(days=1)
# Comments only push: they're frequent, and Resend's free plan allows 100 emails a day.
EMAIL_KINDS = {
    Notification.Kind.TASK_ASSIGNED,
    Notification.Kind.TASK_DUE_SOON,
    Notification.Kind.TASK_OVERDUE,
    Notification.Kind.REPORT_READY,
}


def user_group(user_id: int) -> str:
    return f"user_{user_id}"


def push(user_ids: Iterable[int], kind: str, data: dict) -> None:
    """Send to each person's open sockets. Anyone offline catches up through REST."""
    send = async_to_sync(get_channel_layer().group_send)
    for user_id in user_ids:
        send(user_group(user_id), {"type": "deliver", "kind": kind, "data": data})


def _post(url: str, payload: dict | list, headers: dict | None = None) -> dict:
    response = httpx.post(
        url, json=payload, headers=HEADERS | (headers or {}), timeout=TIMEOUT_SECONDS
    )
    response.raise_for_status()
    return response.json()


def _send_push(notification: Notification) -> None:
    devices = DeviceToken.objects.filter(
        user=notification.recipient_id, user__is_active=True
    ).values_list("token", flat=True)
    tokens = list(devices)
    if not tokens:
        return
    data = {
        "notification": notification.pk,
        "kind": notification.kind,
        "task": notification.task_id,
    }
    messages = [
        {
            "to": token,
            "title": notification.title,
            "body": notification.body,
            "sound": "default",
            "data": data,
        }
        for token in tokens
    ]
    tickets = _post(EXPO_URL, messages)["data"]
    # shortcut: receipts go unread, so a dead token can linger, read them if pushes start failing.
    dead = [
        token
        for token, ticket in zip(tokens, tickets, strict=False)
        if ticket.get("details", {}).get("error") == "DeviceNotRegistered"
    ]
    DeviceToken.objects.filter(token__in=dead).delete()


def _send_email(notification: Notification) -> None:
    recipient = notification.recipient
    if (
        notification.kind not in EMAIL_KINDS
        or not settings.RESEND_API_KEY
        or not recipient.is_active
        # The seed's addresses can't exist, and a bounce counts against the sender.
        or recipient.email.endswith(".example")
    ):
        return
    text = f"{notification.title}: {notification.body}" if notification.body else notification.title
    _post(
        RESEND_URL,
        {
            "from": settings.EMAIL_FROM,
            "to": [recipient.email],
            "subject": notification.title,
            "text": f"{text}\n\nOpen Team Tasks to see it.",
        },
        {
            "Authorization": f"Bearer {settings.RESEND_API_KEY}",
            "Idempotency-Key": f"notification/{notification.pk}",
        },
    )


def _send_once(
    notification: Notification, marker: str, send: Callable[[Notification], None]
) -> None:
    this_notification = Notification.objects.filter(pk=notification.pk)
    if not this_notification.filter(**{marker: None}).update(**{marker: timezone.now()}):
        return
    try:
        send(notification)
    # ValueError and KeyError: a reply that isn't what the provider documents.
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        response = getattr(exc, "response", None)
        logger.warning("%s failed for notification %s: %r", marker, notification.pk, exc)
        # Expo and Resend both say a 4xx won't fix itself, apart from a rate limit.
        if response is None or response.status_code == 429 or response.status_code >= 500:
            this_notification.update(**{marker: None})


def deliver(notification: Notification) -> None:
    """Send each channel still owed. What fails stays owed, for `deliver_pending` to retry."""
    _send_once(notification, "pushed_at", _send_push)
    _send_once(notification, "emailed_at", _send_email)


def deliver_pending() -> None:
    owed = Notification.objects.filter(
        Q(pushed_at=None) | Q(emailed_at=None),
        created_at__gte=timezone.now() - RETRY_WINDOW,
    )
    for notification in owed.select_related("recipient"):
        deliver(notification)


def _announce(notification: Notification) -> None:
    push([notification.recipient_id], "notification", NotificationSerializer(notification).data)
    deliver(notification)


def notify(
    recipient_id: int, kind: str, title: str, *, body: str = "", task: Task | None = None
) -> None:
    def create_and_announce() -> None:
        _announce(
            Notification.objects.create(
                recipient_id=recipient_id, kind=kind, title=title, body=body, task=task
            )
        )

    # robust: a failed notification must not turn an already committed change into an error.
    transaction.on_commit(create_and_announce, robust=True)


def remind(task: Task, kind: str, title: str) -> None:
    """Tell the assignee about this due date once, whichever run gets here first."""
    notification, created = Notification.objects.get_or_create(
        recipient_id=task.assignee_id,
        task=task,
        kind=kind,
        due_at=task.due_at,
        defaults={"title": title, "body": task.title},
    )
    if created:
        _announce(notification)


def notifications_for(user: User, *, unread: bool = False) -> QuerySet[Notification]:
    notifications = Notification.objects.filter(recipient=user).order_by("-created_at", "-id")
    return notifications.filter(read_at__isnull=True) if unread else notifications


def mark_read(user: User, notification_id: int) -> Notification:
    notification = get_object_or_404(Notification, pk=notification_id, recipient=user)
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return notification


def mark_all_read(user: User) -> None:
    Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=timezone.now())


def register_device(user: User, token: str) -> DeviceToken:
    # A shared phone moves to whoever signed in last, so pushes stop reaching the previous user.
    device, _ = DeviceToken.objects.update_or_create(token=token, defaults={"user": user})
    return device


def unregister_device(user: User, token: str) -> None:
    DeviceToken.objects.filter(user=user, token=token).delete()
