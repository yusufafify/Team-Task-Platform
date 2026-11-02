from django.core.management.base import BaseCommand

from apps.notifications import services


class Command(BaseCommand):
    help = "Retry the last day's push and email that a provider missed. Safe to rerun."

    def handle(self, *args, **options):
        services.deliver_pending()
