from datetime import timedelta

import pytest
from django.utils import timezone

from apps.notifications.models import Notification
from apps.tasks.models import Task
from apps.tasks.services import update_task
from tests.factories import MembershipFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db

TASKS = "/api/v1/tasks/"
DONE = Task.Status.DONE


def task_url(task):
    return f"{TASKS}{task.pk}/"


def new_task(team, **overrides):
    return {"team": team.pk, "title": "Ship", "due_at": "2030-01-01T10:00:00Z"} | overrides


def listed_ids(response):
    return {row["id"] for row in response.json()["results"]}


def test_a_leader_creates_a_task(api, team, leader, member):
    response = api(leader).post(TASKS, new_task(team, assignee=member.pk))

    assert response.status_code == 201
    task = Task.objects.get(pk=response.json()["id"])
    assert (task.team, task.created_by, task.assignee) == (team, leader, member)


def test_a_member_cannot_create_a_task(api, team, member):
    assert api(member).post(TASKS, new_task(team)).status_code == 403


def test_an_outsider_cannot_tell_a_real_team_from_a_missing_one(api, team, outsider):
    client = api(outsider)

    real = client.post(TASKS, new_task(team))
    missing = client.post(TASKS, {**new_task(team), "team": 0})

    assert (real.status_code, real.json()) == (missing.status_code, missing.json())
    assert real.status_code == 404


def test_a_task_needs_an_active_assignee_on_the_team(api, team, leader, outsider):
    inactive = MembershipFactory(team=team, user=UserFactory(is_active=False)).user
    client = api(leader)

    for assignee in (outsider, inactive):
        response = client.post(TASKS, new_task(team, assignee=assignee.pk))

        assert response.status_code == 400
        assert "assignee" in response.json()


def test_a_task_created_as_done_gets_a_completion_time(api, team, leader):
    response = api(leader).post(TASKS, new_task(team, status=DONE))

    assert response.status_code == 201
    assert response.json()["completed_at"] is not None


def test_leaders_see_all_team_tasks_and_members_only_their_own(api, team, leader, member):
    mine = TaskFactory(team=team, assignee=member)
    theirs = TaskFactory(team=team)

    assert listed_ids(api(leader).get(TASKS)) == {mine.pk, theirs.pk}
    assert listed_ids(api(member).get(TASKS)) == {mine.pk}


def test_tasks_are_invisible_across_teams(api, team, member, outsider):
    task = TaskFactory(team=team, assignee=member)
    client = api(outsider)

    assert listed_ids(client.get(TASKS)) == set()
    assert client.get(task_url(task)).status_code == 404
    assert client.patch(task_url(task), {"status": DONE}).status_code == 404
    assert client.delete(task_url(task)).status_code == 404


def test_a_member_cannot_reach_a_teammates_task(api, team, member):
    task = TaskFactory(team=team, assignee=MembershipFactory(team=team).user)
    client = api(member)

    assert client.get(task_url(task)).status_code == 404
    assert client.patch(task_url(task), {"status": DONE}).status_code == 404


def test_a_former_member_loses_sight_of_their_finished_tasks(api, team, member):
    task = TaskFactory(team=team, assignee=member, status=DONE, completed_at=timezone.now())
    team.memberships.filter(user=member).delete()

    assert api(member).get(task_url(task)).status_code == 404


def test_a_member_may_change_only_the_status_of_their_task(api, team, member):
    task = TaskFactory(team=team, assignee=member)
    client = api(member)

    assert client.patch(task_url(task), {"status": "in_progress"}).status_code == 200
    assert client.patch(task_url(task), {"title": "Mine"}).status_code == 403
    assert client.patch(task_url(task), {"status": DONE, "assignee": None}).status_code == 403
    task.refresh_from_db()
    assert task.status == Task.Status.IN_PROGRESS
    assert task.title != "Mine"
    assert task.assignee == member


def test_a_leader_edits_every_field_except_the_team(api, team, leader, member):
    task = TaskFactory(team=team)

    response = api(leader).patch(
        task_url(task), {"title": "New", "priority": "urgent", "assignee": member.pk, "team": 0}
    )

    task.refresh_from_db()
    assert response.status_code == 200
    assert (task.title, task.priority, task.assignee) == ("New", "urgent", member)
    assert task.team == team


def test_a_leader_cannot_assign_outside_the_team(api, team, leader, outsider):
    task = TaskFactory(team=team)

    assert api(leader).patch(task_url(task), {"assignee": outsider.pk}).status_code == 400


def test_completion_time_follows_the_status(api, team, member):
    task = TaskFactory(team=team, assignee=member)
    client = api(member)

    first = client.patch(task_url(task), {"status": DONE}).json()["completed_at"]
    again = client.patch(task_url(task), {"status": DONE}).json()["completed_at"]
    reopened = client.patch(task_url(task), {"status": "todo"}).json()["completed_at"]

    assert first is not None
    assert again == first
    assert reopened is None


def test_a_stale_status_change_keeps_a_leaders_newer_edit(team, member):
    task = TaskFactory(team=team, assignee=member, title="Old")
    stale = Task.objects.get(pk=task.pk)
    Task.objects.filter(pk=task.pk).update(title="New")

    update_task(member, stale, status=Task.Status.BLOCKED)

    task.refresh_from_db()
    assert (task.title, task.status) == ("New", Task.Status.BLOCKED)


def test_a_stale_edit_keeps_a_completion_that_happened_meanwhile(team, leader, member):
    task = TaskFactory(team=team, assignee=member)
    stale = Task.objects.get(pk=task.pk)
    update_task(member, task, status=DONE)

    update_task(leader, stale, title="New")

    task.refresh_from_db()
    assert (task.title, task.status) == ("New", DONE)
    assert task.completed_at is not None


def test_a_maximum_length_title_still_notifies(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    title = "x" * 200

    with django_capture_on_commit_callbacks(execute=True):
        api(leader).post(TASKS, new_task(team, title=title, assignee=member.pk))

    assert Notification.objects.get().body == title


def test_an_edit_bumps_updated_at(api, team, member):
    task = TaskFactory(team=team, assignee=member)

    api(member).patch(task_url(task), {"status": "blocked"})

    previous = task.updated_at
    task.refresh_from_db()
    assert task.updated_at > previous


def test_only_a_leader_deletes_a_task(api, team, leader, member):
    task = TaskFactory(team=team, assignee=member)

    assert api(member).delete(task_url(task)).status_code == 403
    assert api(leader).delete(task_url(task)).status_code == 204
    assert not Task.objects.filter(pk=task.pk).exists()


def test_put_is_not_offered(api, team, leader):
    task = TaskFactory(team=team)

    assert api(leader).put(task_url(task), new_task(team)).status_code == 405


def test_assignment_notifies_the_new_assignee_after_commit(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        response = api(leader).post(TASKS, new_task(team, assignee=member.pk))

    notification = Notification.objects.get()
    assert notification.recipient == member
    assert notification.kind == Notification.Kind.TASK_ASSIGNED
    assert notification.task_id == response.json()["id"]


def test_self_assignment_and_unrelated_edits_stay_quiet(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        created = api(leader).post(TASKS, new_task(team, assignee=leader.pk)).json()
        api(leader).patch(f"{TASKS}{created['id']}/", {"title": "New", "assignee": leader.pk})

    assert not Notification.objects.exists()


def test_reassignment_notifies_only_the_new_assignee(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    task = TaskFactory(team=team, assignee=leader)

    with django_capture_on_commit_callbacks(execute=True):
        api(leader).patch(task_url(task), {"assignee": member.pk})

    assert Notification.objects.get().recipient == member


def test_list_filters(api, team, leader, member):
    now = timezone.now()
    overdue = TaskFactory(team=team, due_at=now - timedelta(days=1), assignee=member)
    upcoming = TaskFactory(team=team, due_at=now + timedelta(days=1), priority="urgent")
    finished = TaskFactory(team=team, due_at=now - timedelta(days=1), status=DONE, completed_at=now)
    TaskFactory(team=MembershipFactory(user=leader).team)
    client = api(leader)

    assert listed_ids(client.get(TASKS, {"overdue": "true"})) == {overdue.pk}
    assert listed_ids(client.get(TASKS, {"status": DONE})) == {finished.pk}
    assert listed_ids(client.get(TASKS, {"priority": "urgent"})) == {upcoming.pk}
    assert listed_ids(client.get(TASKS, {"assignee": member.pk})) == {overdue.pk}
    assert listed_ids(client.get(TASKS, {"team": team.pk})) == {
        overdue.pk,
        upcoming.pk,
        finished.pk,
    }


@pytest.mark.parametrize("query", [{"team": "abc"}, {"status": "nope"}, {"assignee": "x"}])
def test_a_bad_filter_is_a_client_error(api, leader, query):
    assert api(leader).get(TASKS, query).status_code == 400


def test_a_task_reports_whether_it_is_overdue(api, team, leader):
    now = timezone.now()
    late = TaskFactory(team=team, due_at=now - timedelta(days=1))
    finished = TaskFactory(team=team, due_at=now - timedelta(days=1), status=DONE, completed_at=now)
    client = api(leader)

    assert client.get(task_url(late)).json()["is_overdue"] is True
    assert client.get(task_url(finished)).json()["is_overdue"] is False


def test_lists_are_paginated_with_earliest_due_first(api, team, leader):
    now = timezone.now()
    tasks = [TaskFactory(team=team, due_at=now + timedelta(hours=n)) for n in range(21)]

    page = api(leader).get(TASKS).json()

    assert page["count"] == 21
    assert page["next"] is not None
    assert [row["id"] for row in page["results"]] == [task.pk for task in tasks[:20]]
