from datetime import timedelta
from io import StringIO

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.db.models import F

from apps.chat.models import Message
from apps.tasks.models import Comment, Task
from apps.tasks.services import overdue_filter, team_stats, visible_tasks
from apps.teams.models import Team, TeamMembership
from tests.factories import MembershipFactory, TaskFactory, TeamFactory

pytestmark = pytest.mark.django_db

User = get_user_model()


def seed():
    call_command("seed_demo", stdout=StringIO())


def demo_team():
    return Team.objects.get(memberships__user__email="mona@demo.example")


def counts():
    return [m.objects.count() for m in (User, Team, TeamMembership, Task, Comment, Message)]


def test_seeding_twice_adds_nothing():
    seed()
    first = counts()

    seed()

    assert counts() == first


def test_seeding_again_moves_the_dates_forward():
    seed()
    task = Task.objects.get(title="Renew the SSL certificate")
    Task.objects.filter(pk=task.pk).update(due_at=F("due_at") - timedelta(days=30))

    seed()

    refreshed = Task.objects.get(pk=task.pk)
    assert refreshed.due_at > task.due_at - timedelta(days=1)


def test_the_team_has_one_leader_and_members_with_names():
    seed()

    memberships = demo_team().memberships.select_related("user")

    roles = sorted(membership.role for membership in memberships)
    assert roles == ["leader", "member", "member", "member"]
    assert all(membership.user.get_full_name() for membership in memberships)


def test_the_data_shows_every_case_the_assistant_talks_about():
    seed()

    tasks = demo_team().tasks

    assert tasks.filter(overdue_filter()).exists()
    assert tasks.filter(assignee__isnull=True).exists()
    assert {task.status for task in tasks.all()} == set(Task.Status.values)
    assert tasks.filter(completed_at__gt=F("due_at")).exists()
    assert tasks.filter(completed_at__lte=F("due_at")).exists()


def test_seeded_people_go_through_the_normal_scoping():
    seed()
    leader = User.objects.get(email="mona@demo.example")
    member = User.objects.get(email="sara@demo.example")

    assert visible_tasks(leader).count() == Task.objects.count()
    assert visible_tasks(member).count() < Task.objects.count()
    assert team_stats(member, demo_team().pk)["scope"] == "self"


def test_a_real_team_with_the_same_name_is_left_alone():
    real = TeamFactory(name="Demo Team")
    MembershipFactory(team=real)
    task = TaskFactory(team=real, title="Prepare the Q4 budget review")

    seed()

    task.refresh_from_db()
    assert task.team == real
    assert real.memberships.count() == 1
    assert demo_team() != real


def test_with_no_password_set_the_accounts_cannot_log_in(settings):
    settings.SEED_USER_PASSWORD = None

    seed()

    assert not User.objects.get(email="mona@demo.example").has_usable_password()


def test_a_set_password_logs_in(settings):
    settings.SEED_USER_PASSWORD = "demo-only-x9!kQ2"

    seed()

    assert authenticate(username="sara@demo.example", password="demo-only-x9!kQ2")
