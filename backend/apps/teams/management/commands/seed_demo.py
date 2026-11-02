from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.chat.models import Message
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
# Title, description, assignee, status, priority, days until due, days until completed.
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
    ("Audit last quarter's expenses", "", "omar", "done", "low", -35, -34),
]
# Task title, author, body.
COMMENTS = [
    ("Renew the SSL certificate", "omar", "Waiting for DNS access from IT."),
    ("Renew the SSL certificate", "mona", "I'll chase them tomorrow."),
    ("Fix the login timeout on mobile", "sara", "It only happens on Android."),
]
# Author, body.
MESSAGES = [
    ("mona", "Morning all, standup moves to 10:30 tomorrow."),
    ("omar", "I'm blocked on the SSL renewal until IT answers."),
    ("sara", "The release notes are out."),
]


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
        tasks = {}
        for title, description, assignee, status, priority, due_in, completed_in in TASKS:
            tasks[title], _ = Task.objects.update_or_create(
                team=team,
                title=title,
                defaults={
                    "description": description,
                    "assignee": users.get(assignee),
                    "created_by": leader,
                    "status": status,
                    "priority": priority,
                    "due_at": now + timedelta(days=due_in),
                    # Written directly, so it must stay set exactly when the status is done.
                    "completed_at": now + timedelta(days=completed_in) if completed_in else None,
                },
            )
        for title, author, body in COMMENTS:
            Comment.objects.get_or_create(task=tasks[title], author=users[author], body=body)
        for author, body in MESSAGES:
            Message.objects.get_or_create(team=team, author=users[author], body=body)
        self.stdout.write(f"{team.name}: {len(users)} people and {len(tasks)} tasks.")
