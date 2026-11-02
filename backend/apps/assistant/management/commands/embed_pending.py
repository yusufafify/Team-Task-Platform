from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import Throttled

from apps.ai.services import AIUnavailable
from apps.assistant import retrieval
from apps.teams.models import Team


class Command(BaseCommand):
    help = "Embed every task, comment and chat message not yet searchable. Safe to rerun."

    def handle(self, *args, **options):
        for team in Team.objects.order_by("pk"):
            try:
                while count := retrieval.sync(team):
                    self.stdout.write(f"{team}: embedded {count}")
            except (Throttled, AIUnavailable) as exc:
                raise CommandError(f"Stopped at {team}: {exc.detail} Run it again later.") from exc
