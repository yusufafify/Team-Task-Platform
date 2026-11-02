from django.db import models
from django.db.models import Q
from pgvector.django import VectorField


class Embedding(models.Model):
    """The vector for one task, comment or chat message, so a search can rank them by meaning.

    Holds no text: `retrieval.search` reads each result from its source, so it's always current.
    """

    DIMENSIONS = 768

    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE)
    task = models.OneToOneField("tasks.Task", on_delete=models.CASCADE, null=True, blank=True)
    comment = models.OneToOneField("tasks.Comment", on_delete=models.CASCADE, null=True, blank=True)
    message = models.OneToOneField("chat.Message", on_delete=models.CASCADE, null=True, blank=True)
    # MD5 of the model and the text, so changing either embeds the row again.
    digest = models.CharField(max_length=32)
    vector = VectorField(dimensions=DIMENSIONS)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(task__isnull=False, comment__isnull=True, message__isnull=True)
                | Q(task__isnull=True, comment__isnull=False, message__isnull=True)
                | Q(task__isnull=True, comment__isnull=True, message__isnull=False),
                name="embedding_has_one_source",
            ),
        ]

    def __str__(self):
        return f"Embedding {self.pk}"


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
