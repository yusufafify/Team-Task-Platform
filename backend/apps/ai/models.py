from django.conf import settings
from django.db import models


class AICall(models.Model):
    """One request to the LLM, and the rate limits' counter. Never stores a prompt or a reply."""

    class Feature(models.TextChoices):
        CHAT = "chat", "Chat"
        REPORT = "report", "Report"
        EMBED = "embed", "Embedding"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    feature = models.CharField(max_length=20, choices=Feature)
    model = models.CharField(max_length=100)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    team = models.ForeignKey("teams.Team", on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    error = models.CharField(max_length=500, blank=True)
    input_tokens = models.PositiveIntegerField(null=True, blank=True)
    output_tokens = models.PositiveIntegerField(null=True, blank=True)
    total_tokens = models.PositiveIntegerField(null=True, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["created_at"])]
        verbose_name = "AI call"

    def __str__(self):
        return f"{self.feature} call, {self.status}"
