import pytest

from apps.notifications.models import Notification
from apps.tasks.models import Comment
from tests.factories import CommentFactory, MembershipFactory, TaskFactory

pytestmark = pytest.mark.django_db


def comments_url(task):
    return f"/api/v1/tasks/{task.pk}/comments/"


def test_a_member_comments_on_their_task_as_themselves(api, team, member):
    task = TaskFactory(team=team, assignee=member)

    response = api(member).post(comments_url(task), {"body": "Done soon", "author": 999})

    assert response.status_code == 201
    assert response.json()["author"]["id"] == member.pk
    assert Comment.objects.get().task == task


def test_comments_list_oldest_first_for_the_leader(api, team, leader, member):
    task = TaskFactory(team=team, assignee=member)
    first = CommentFactory(task=task, author=member)
    second = CommentFactory(task=task, author=leader)

    response = api(leader).get(comments_url(task))

    assert [row["id"] for row in response.json()["results"]] == [first.pk, second.pk]


def test_comments_are_invisible_outside_the_tasks_audience(api, team, member, outsider):
    task = TaskFactory(team=team, assignee=MembershipFactory(team=team).user)
    CommentFactory(task=task)

    for user in (member, outsider):
        assert api(user).get(comments_url(task)).status_code == 404
        assert api(user).post(comments_url(task), {"body": "Hi"}).status_code == 404
    assert Comment.objects.count() == 1


@pytest.mark.parametrize("body", ["", "   ", "x" * 5001])
def test_a_comment_needs_a_reasonable_body(api, team, leader, body):
    task = TaskFactory(team=team)

    assert api(leader).post(comments_url(task), {"body": body}).status_code == 400


def test_a_comment_notifies_the_assignee_and_creator_but_not_the_author(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    task = TaskFactory(team=team, created_by=leader, assignee=member)

    with django_capture_on_commit_callbacks(execute=True):
        api(member).post(comments_url(task), {"body": "Blocked on data"})

    notification = Notification.objects.get()
    assert notification.recipient == leader
    assert notification.kind == Notification.Kind.TASK_COMMENTED


def test_a_comment_does_not_notify_someone_who_left_the_team(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    task = TaskFactory(team=team, created_by=member)
    team.memberships.filter(user=member).delete()

    with django_capture_on_commit_callbacks(execute=True):
        api(leader).post(comments_url(task), {"body": "Picking this up"})

    assert not Notification.objects.exists()
