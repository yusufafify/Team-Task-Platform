from django.db import models


class AssistantMessage(models.Model):
    """One side of a person's private conversation with the assistant, on one team."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    # The membership, not a team and a user, so a thread can't outlive a place on the team.
    membership = models.ForeignKey(
        "teams.TeamMembership", on_delete=models.CASCADE, related_name="assistant_messages"
    )
    role = models.CharField(max_length=10, choices=Role)
    body = models.TextField()
    # Set only on answers that may be reused. `services.ask` explains which ones.
    cache_key = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role} message"
