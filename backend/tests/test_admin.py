import pytest
from django.contrib.auth import authenticate
from django.urls import reverse

from apps.chat.models import Message
from apps.notifications.models import DeviceToken, Notification
from apps.tasks.models import Comment
from apps.teams.models import TeamMembership
from tests.factories import TaskFactory, UserFactory

pytestmark = pytest.mark.django_db

PASSWORD = "x9!kQ2vLm-long"
USER_ADD = "admin:accounts_user_add"


def user_form(email: str) -> dict[str, str]:
    return {
        "email": email,
        "usable_password": "true",
        "password1": PASSWORD,
        "password2": PASSWORD,
    }


@pytest.fixture
def rows():
    task = TaskFactory(assignee=UserFactory())
    author = task.created_by
    TeamMembership.objects.create(team=task.team, user=author)
    return {
        "accounts_user": author,
        "teams_team": task.team,
        "tasks_task": task,
        "tasks_comment": Comment.objects.create(task=task, author=author, body="On it"),
        "chat_message": Message.objects.create(team=task.team, author=author, body="Hello"),
        "notifications_notification": Notification.objects.create(
            recipient=author, kind=Notification.Kind.TASK_ASSIGNED, title="New task", task=task
        ),
        "notifications_devicetoken": DeviceToken.objects.create(
            user=author, token="ExponentPushToken[abc-123]"
        ),
    }


@pytest.mark.parametrize(
    "model",
    [
        "accounts_user",
        "teams_team",
        "tasks_task",
        "tasks_comment",
        "chat_message",
        "notifications_notification",
        "notifications_devicetoken",
    ],
)
def test_admin_pages_open(admin_client, rows, model):
    for page, args in (("changelist", []), ("add", []), ("change", [rows[model].pk])):
        url = reverse(f"admin:{model}_{page}", args=args)
        assert admin_client.get(url).status_code == 200, url


def test_admin_refuses_anonymous_visitors(client):
    response = client.get(reverse("admin:tasks_task_changelist"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


def test_admin_refuses_non_staff_users(client):
    client.force_login(UserFactory())

    response = client.get(reverse("admin:tasks_task_changelist"))

    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


def test_admin_creates_a_user_who_can_log_in(admin_client):
    response = admin_client.post(reverse(USER_ADD), user_form("New.Person@Example.com"))

    assert response.status_code == 302
    assert authenticate(username="new.person@example.com", password=PASSWORD)


def test_admin_reports_a_duplicate_email_whatever_its_case(admin_client):
    UserFactory(email="taken@example.com")

    response = admin_client.post(reverse(USER_ADD), user_form("TAKEN@example.com"))

    assert response.status_code == 200
    assert "email" in response.context["adminform"].form.errors
