from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

expo_token_validator = RegexValidator(
    r"^Expo(nent)?PushToken\[[^\]]+\]\Z", "Enter a valid Expo push token."
)


class Notification(models.Model):
    class Kind(models.TextChoices):
        TASK_ASSIGNED = "task_assigned", "Task assigned"
        TASK_COMMENTED = "task_commented", "Task commented"
        TASK_DUE_SOON = "task_due_soon", "Task due soon"
        TASK_OVERDUE = "task_overdue", "Task overdue"
        REPORT_READY = "report_ready", "Report ready"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    kind = models.CharField(max_length=30, choices=Kind)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    task = models.ForeignKey(
        "tasks.Task",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
    )
    # Set only on reminders: the due date this one was about, so a new date earns a new reminder.
    due_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    # Null means still owed. Set before sending, so overlapping runs can't both send.
    pushed_at = models.DateTimeField(null=True, blank=True)
    emailed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["recipient", "-created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["recipient", "task", "kind", "due_at"],
                condition=models.Q(due_at__isnull=False),
                name="unique_reminder",
            )
        ]

    def __str__(self):
        return f"{self.kind} for {self.recipient}"


class DeviceToken(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    token = models.CharField(max_length=255, unique=True, validators=[expo_token_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Device of {self.user}"
