import json
from datetime import UTC, datetime, timedelta
from io import StringIO

import pytest
from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.db.models import F
from django.utils import timezone

from apps.ai import provider
from apps.chat.models import Message
from apps.reports.services import write_report
from apps.tasks.models import Comment, Task
from apps.tasks.services import overdue_filter, team_stats, visible_tasks
from apps.teams.models import Team, TeamMembership
from tests.factories import MembershipFactory, TaskFactory, TeamFactory

pytestmark = pytest.mark.django_db

User = get_user_model()

# The dates a calendar can make awkward.
DATES = [
    pytest.param(datetime(2026, 11, 2, 12, tzinfo=UTC), id="just-after-a-month-ended"),
    pytest.param(datetime(2026, 10, 31, 20, tzinfo=UTC), id="the-last-day-of-a-month"),
    pytest.param(datetime(2026, 11, 20, 12, tzinfo=UTC), id="mid-month"),
    pytest.param(datetime(2026, 3, 1, 12, tzinfo=UTC), id="after-the-shortest-month"),
    pytest.param(datetime(2027, 1, 1, 12, tzinfo=UTC), id="across-a-year"),
]


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


def test_seeding_in_a_later_month_moves_the_rows_instead_of_adding(monkeypatch):
    monkeypatch.setattr(timezone, "now", lambda: datetime(2026, 11, 2, 12, tzinfo=UTC))
    seed()
    first = counts()

    monkeypatch.setattr(timezone, "now", lambda: datetime(2026, 12, 2, 12, tzinfo=UTC))
    seed()

    assert counts() == first
    assert demo_team().messages.filter(created_at__month=11).exists()


@pytest.mark.parametrize("now", DATES)
def test_the_last_complete_month_has_a_real_report_on_any_date(monkeypatch, settings, now):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    monkeypatch.setattr(timezone, "now", lambda: now)
    sent = []

    def fake_send(prompt, **options):
        sent.append(json.loads(prompt))
        return provider.Reply("completed", "A good month.", [], 10, 2, 15)

    monkeypatch.setattr(provider, "send", fake_send)
    seed()

    assert write_report(demo_team())
    data = sent[0]
    assert data["comments"]["total"] >= 4
    assert data["messages"]["total"] >= 4
    assert data["stats"]["completed"] >= 4
    assert data["stats"]["delayed"] >= 1
    assert data["stats"]["overdue"] >= 1


@pytest.mark.parametrize("now", DATES)
def test_no_date_contradicts_another(monkeypatch, now):
    monkeypatch.setattr(timezone, "now", lambda: now)

    seed()

    assert not Task.objects.filter(completed_at__gt=now).exists()
    assert not Task.objects.filter(created_at__gt=now).exists()
    assert not Task.objects.filter(created_at__gt=F("due_at")).exists()
    assert not Task.objects.filter(created_at__gt=F("completed_at")).exists()
    assert not Comment.objects.filter(created_at__gt=now).exists()
    assert not Comment.objects.filter(created_at__lt=F("task__created_at")).exists()
    assert not Message.objects.filter(created_at__gt=now).exists()


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
