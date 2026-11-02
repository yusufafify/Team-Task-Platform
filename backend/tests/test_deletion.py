"""History keeps its people and its team. Join rows and per-user rows go with their parent."""

import pytest
from django.db.models import ProtectedError

from apps.chat.models import Message
from apps.notifications.models import DeviceToken, Notification
from apps.reports.models import MonthlyReport
from apps.tasks.models import Comment, Task
from apps.teams.models import TeamMembership
from tests.factories import ReportFactory, TaskFactory, TeamFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_a_teams_reports_go_with_it():
    report = ReportFactory()

    report.team.delete()

    assert not MonthlyReport.objects.exists()


@pytest.mark.parametrize("field", ["assignee", "created_by"])
def test_user_on_a_task_cannot_be_deleted(field):
    user = UserFactory()
    TaskFactory(**{field: user})

    with pytest.raises(ProtectedError):
        user.delete()


def test_comment_author_cannot_be_deleted():
    author = UserFactory()
    Comment.objects.create(task=TaskFactory(), author=author, body="On it")

    with pytest.raises(ProtectedError):
        author.delete()


def test_message_author_cannot_be_deleted():
    author = UserFactory()
    Message.objects.create(team=TeamFactory(), author=author, body="Hello")

    with pytest.raises(ProtectedError):
        author.delete()


def test_team_with_tasks_cannot_be_deleted():
    task = TaskFactory()

    with pytest.raises(ProtectedError):
        task.team.delete()


def test_team_with_messages_cannot_be_deleted():
    message = Message.objects.create(team=TeamFactory(), author=UserFactory(), body="Hello")

    with pytest.raises(ProtectedError):
        message.team.delete()


def test_deleting_an_empty_team_removes_its_memberships():
    team = TeamFactory()
    TeamMembership.objects.create(team=team, user=UserFactory())

    team.delete()

    assert not TeamMembership.objects.exists()


def test_deleting_a_user_without_history_removes_their_personal_rows():
    user = UserFactory()
    TeamMembership.objects.create(team=TeamFactory(), user=user)
    DeviceToken.objects.create(user=user, token="ExponentPushToken[abc-123]")
    Notification.objects.create(
        recipient=user, kind=Notification.Kind.TASK_ASSIGNED, title="New task"
    )

    user.delete()

    assert not TeamMembership.objects.exists()
    assert not DeviceToken.objects.exists()
    assert not Notification.objects.exists()


def test_deleting_a_task_removes_its_comments_and_notifications():
    task = TaskFactory()
    Comment.objects.create(task=task, author=task.created_by, body="On it")
    Notification.objects.create(
        recipient=task.created_by, kind=Notification.Kind.TASK_COMMENTED, title="Reply", task=task
    )

    task.delete()

    assert not Task.objects.exists()
    assert not Comment.objects.exists()
    assert not Notification.objects.exists()
