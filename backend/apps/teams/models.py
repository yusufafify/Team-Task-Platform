from zoneinfo import available_timezones

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


def validate_timezone(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError(f"{value} is not a known timezone.")


class Team(models.Model):
    name = models.CharField(max_length=150)
    timezone = models.CharField(
        max_length=64, default="Africa/Cairo", validators=[validate_timezone]
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="TeamMembership", related_name="teams"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TeamMembership(models.Model):
    class Role(models.TextChoices):
        LEADER = "leader", "Leader"
        MEMBER = "member", "Member"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships"
    )
    role = models.CharField(max_length=10, choices=Role, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["team", "user"], name="unique_team_member")]

    def __str__(self):
        return f"{self.user} in {self.team} ({self.role})"
