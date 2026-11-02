from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import Throttled

from apps.ai.services import AIUnavailable
from apps.reports import services
from apps.teams.models import Team


class Command(BaseCommand):
    help = "Write each team's report for its last complete month. Safe to rerun."

    def handle(self, *args, **options):
        for team in Team.objects.order_by("pk"):
            try:
                report = services.write_report(team)
            except (Throttled, AIUnavailable) as exc:
                raise CommandError(f"Stopped at {team}: {exc.detail} Run it again later.") from exc
            if report:
                self.stdout.write(f"{team}: wrote {report.month:%B %Y}")
