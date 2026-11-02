from django.core.management.base import BaseCommand

from apps.tasks import services


class Command(BaseCommand):
    help = "Remind assignees of tasks due soon or overdue, once per due date. Safe to rerun."

    def handle(self, *args, **options):
        services.send_reminders()
