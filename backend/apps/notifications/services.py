from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone
from rest_framework.generics import get_object_or_404

from apps.notifications.models import DeviceToken, Notification
from apps.tasks.models import Task

User = get_user_model()


def notify(
    recipient_id: int, kind: str, title: str, *, body: str = "", task: Task | None = None
) -> None:
    # robust: a failed notification must not turn an already committed change into an error.
    transaction.on_commit(
        lambda: Notification.objects.create(
            recipient_id=recipient_id, kind=kind, title=title, body=body, task=task
        ),
        robust=True,
    )


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
