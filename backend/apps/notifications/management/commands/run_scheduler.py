import asyncio

from django.core.management.base import BaseCommand

from config import scheduler


class Command(BaseCommand):
    help = (
        "Run the schedule as its own process, for when servers share a channel layer. "
        "Set SCHEDULER_IN_SERVER=false on them first, because the schedule must run only once."
    )

    def handle(self, *args, **options):
        asyncio.run(scheduler.run_forever())
