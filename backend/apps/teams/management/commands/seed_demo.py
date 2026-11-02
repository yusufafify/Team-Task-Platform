from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.chat.models import Message
from apps.reports.services import last_complete_month
from apps.tasks.models import Comment, Task
from apps.teams.models import Team, TeamMembership

User = get_user_model()
TEAM_NAME = "Demo Team"
EMAIL_DOMAIN = "demo.example"
LEADER = "mona"
# Key, first name, last name.
PEOPLE = [
    (LEADER, "Mona", "Hassan"),
    ("sara", "Sara", "Ali"),
    ("omar", "Omar", "Khaled"),
    ("nour", "Nour", "Adel"),
]
# Days count from an anchor: today for what's on the board now, and the first day of the last
# complete month for what its report reads. Under 28 there, so that month's rows fit in February.
# Title, description, assignee, status, priority, days to due, days to completed.
TASKS = [
    ("Prepare the Q4 budget review", "Compare spend.", "sara", "in_progress", "high", 2, None),
    ("Fix the login timeout on mobile", "", "omar", "in_progress", "urgent", -1, None),
    ("Update the onboarding guide", "", "nour", "todo", "medium", 6, None),
    ("Renew the SSL certificate", "It expires soon.", "omar", "blocked", "high", -3, None),
    ("Plan the team offsite", "", "sara", "todo", "low", 14, None),
    ("Review the vendor contract", "Legal comments first.", "mona", "todo", "high", 1, None),
    ("Draft the customer survey", "", None, "todo", "low", 10, None),
    ("Migrate reports to the new template", "", "nour", "done", "medium", -5, -6),
    ("Write the release notes for 2.4", "", "sara", "done", "medium", -4, -2),
]
LAST_MONTH_TASKS = [
    ("Audit last quarter's expenses", "", "omar", "done", "low", 18, 17),
    ("Book the auditors for the year-end review", "", "mona", "done", "medium", 9, 9),
    ("Clean up the supplier list", "Drop anyone unused.", "nour", "done", "low", 12, 15),
    ("Run the fire safety drill", "", "sara", "done", "high", 14, 13),
    ("Replace the shared printer", "Quotes are in.", "nour", "blocked", "medium", 20, None),
    ("Roll out the new VPN client", "", "omar", "in_progress", "high", 24, None),
]
# Task title, author, body, days to written.
COMMENTS = [
    ("Renew the SSL certificate", "omar", "Waiting for DNS access from IT.", -3),
    ("Renew the SSL certificate", "mona", "I'll chase them tomorrow.", -2.9),
    ("Fix the login timeout on mobile", "sara", "It only happens on Android.", -1),
]
LAST_MONTH_COMMENTS = [
    ("Clean up the supplier list", "nour", "Three suppliers had no contact on file.", 14),
    ("Replace the shared printer", "nour", "The vendor needs a purchase order first.", 16),
    ("Replace the shared printer", "mona", "Finance has the order, I'll chase them.", 17),
    ("Roll out the new VPN client", "omar", "Older laptops need an OS update first.", 22),
]
# Author, body, days to written.
MESSAGES = [
    ("sara", "The release notes are out.", -2),
    ("mona", "Morning all, standup moves to 10:30 tomorrow.", -1),
    ("omar", "I'm blocked on the SSL renewal until IT answers.", -0.8),
]
LAST_MONTH_MESSAGES = [
    ("mona", "Please send your month-end figures by the 25th.", 4),
    ("sara", "The fire drill is booked for the 14th.", 10),
    ("omar", "The VPN rollout starts this week, expect a short outage.", 18),
    ("nour", "The printer is still stuck on the purchase order.", 21),
]


def backdate(row, moment):
    # By update, because auto_now_add overwrites anything set on the instance.
    type(row).objects.filter(pk=row.pk).update(created_at=moment)


class Command(BaseCommand):
    help = "Create or refresh a small demo team, for trying the app before clients can add data."

    @transaction.atomic
    def handle(self, *args, **options):
        users = {}
        for key, first_name, last_name in PEOPLE:
            users[key], _ = User.objects.get_or_create(
                email=f"{key}@{EMAIL_DOMAIN}",
                defaults={"first_name": first_name, "last_name": last_name},
            )
            # With no value set, this leaves an account that can't log in.
            users[key].set_password(settings.SEED_USER_PASSWORD)
            users[key].save(update_fields=["password"])
        leader = users[LEADER]

        # Found through its leader, so a real team with this name is never touched.
        team = Team.objects.filter(name=TEAM_NAME, memberships__user=leader).first()
        team = team or Team.objects.create(name=TEAM_NAME)
        for key, user in users.items():
            role = TeamMembership.Role.LEADER if key == LEADER else TeamMembership.Role.MEMBER
            TeamMembership.objects.update_or_create(team=team, user=user, defaults={"role": role})

        now = timezone.now()
        zone = ZoneInfo(team.timezone)
        month_start = datetime.combine(last_complete_month(team), time(9), tzinfo=zone)
        tasks = {}
        for anchor, task_rows, comment_rows, message_rows in (
            (month_start, LAST_MONTH_TASKS, LAST_MONTH_COMMENTS, LAST_MONTH_MESSAGES),
            (now, TASKS, COMMENTS, MESSAGES),
        ):
            for title, description, assignee, status, priority, due_in, completed_in in task_rows:
                due = anchor + timedelta(days=due_in)
                # Written directly, so it must stay set exactly when the status is done.
                completed = None if completed_in is None else anchor + timedelta(days=completed_in)
                tasks[title], _ = Task.objects.update_or_create(
                    team=team,
                    title=title,
                    defaults={
                        "description": description,
                        "assignee": users.get(assignee),
                        "created_by": leader,
                        "status": status,
                        "priority": priority,
                        "due_at": due,
                        "completed_at": completed,
                    },
                )
                created = min(due, completed or due, now) - timedelta(days=7)
                backdate(tasks[title], created)
            for title, author, body, written_in in comment_rows:
                comment, _ = Comment.objects.get_or_create(
                    task=tasks[title], author=users[author], body=body
                )
                backdate(comment, anchor + timedelta(days=written_in))
            for author, body, written_in in message_rows:
                message, _ = Message.objects.get_or_create(
                    team=team, author=users[author], body=body
                )
                backdate(message, anchor + timedelta(days=written_in))
        self.stdout.write(f"{team.name}: {len(users)} people and {len(tasks)} tasks.")
