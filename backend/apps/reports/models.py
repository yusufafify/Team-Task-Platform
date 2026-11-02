from django.db import models


class MonthlyReport(models.Model):
    """One team's month, frozen when written, so later edits to tasks don't rewrite history."""

    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE, related_name="reports")
    month = models.DateField(help_text="First day of the month, in the team's timezone.")
    stats = models.JSONField()
    members = models.JSONField()
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Run-once lives here, not in timing, because two schedulers can overlap in a deploy.
            models.UniqueConstraint(fields=["team", "month"], name="unique_team_month_report")
        ]

    def __str__(self):
        return f"{self.team}, {self.month:%B %Y}"
