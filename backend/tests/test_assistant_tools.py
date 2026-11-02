import json
from datetime import UTC, datetime, timedelta

import pytest
from django.utils import timezone

from apps.assistant import tools
from apps.tasks.models import Task
from apps.teams.models import TeamMembership
from tests.factories import (
    CommentFactory,
    MembershipFactory,
    MessageFactory,
    TaskFactory,
    UserFactory,
)

pytestmark = pytest.mark.django_db


def call(user, team, name, /, **arguments):
    step = {"type": "function_call", "id": "c1", "name": name, "arguments": arguments}
    return tools.run(user, team, step)


def result(user, team, name, /, **arguments):
    step = call(user, team, name, **arguments)
    assert step["is_error"] is False, step
    return json.loads(step["result"][0]["text"])


def refusal(user, team, name, /, **arguments):
    step = call(user, team, name, **arguments)
    assert step["is_error"] is True, step
    return step["result"][0]["text"]


def ids(rows):
    return [row["id"] for row in rows]


@pytest.fixture
def tasks(team, leader, member):
    """One task for the member and one for the leader, so a member's view shows a difference."""
    return {
        "mine": TaskFactory(team=team, created_by=leader, assignee=member, title="Mine"),
        "theirs": TaskFactory(team=team, created_by=leader, assignee=leader, title="Theirs"),
    }


# Shape


def test_every_tool_is_declared_for_the_model():
    assert {declaration["name"] for declaration in tools.DECLARATIONS} == set(tools.TOOLS)


def test_a_tool_result_answers_the_call_that_asked(team, leader):
    step = call(leader, team, "list_tasks")

    assert (step["type"], step["call_id"], step["name"]) == ("function_result", "c1", "list_tasks")


@pytest.mark.parametrize("name", [None, "", "delete_task", "__class__"])
def test_a_made_up_tool_is_refused_not_raised(team, leader, name):
    assert "no tool" in refusal(leader, team, name)


def test_a_call_with_no_arguments_still_runs(team, leader):
    step = {"type": "function_call", "id": "c1", "name": "list_tasks"}

    assert tools.run(leader, team, step)["is_error"] is False


# list_tasks


def test_a_leader_lists_the_whole_team(team, leader, tasks):
    assert result(leader, team, "list_tasks")["total"] == 2


def test_a_member_lists_only_their_own_tasks(team, member, tasks):
    assert ids(result(member, team, "list_tasks")["tasks"]) == [tasks["mine"].pk]


def test_the_model_cannot_point_list_tasks_at_another_team(team, leader, tasks):
    other = MembershipFactory(user=leader, role=TeamMembership.Role.LEADER).team
    TaskFactory(team=other, created_by=leader, title="Elsewhere")

    rows = result(leader, team, "list_tasks", team=other.pk)["tasks"]

    assert "Elsewhere" not in [row["title"] for row in rows]


def test_list_tasks_filters(team, leader, member):
    wanted = TaskFactory(
        team=team, created_by=leader, assignee=member, priority=Task.Priority.URGENT
    )
    TaskFactory(team=team, created_by=leader, assignee=leader, priority=Task.Priority.LOW)

    assert ids(result(leader, team, "list_tasks", priority="urgent")["tasks"]) == [wanted.pk]
    assert ids(result(leader, team, "list_tasks", assignee=member.pk)["tasks"]) == [wanted.pk]


def test_list_tasks_finds_overdue_work(team, leader):
    late = TaskFactory(team=team, created_by=leader, due_at=timezone.now() - timedelta(days=1))
    TaskFactory(team=team, created_by=leader, due_at=timezone.now() + timedelta(days=1))

    rows = result(leader, team, "list_tasks", overdue=True)["tasks"]

    assert ids(rows) == [late.pk]
    assert rows[0]["overdue"] is True


def test_list_tasks_refuses_a_status_that_does_not_exist(team, leader):
    assert "status" in refusal(leader, team, "list_tasks", status="abandoned")


def test_list_tasks_caps_its_rows_and_reports_the_total(team, leader, monkeypatch):
    monkeypatch.setattr(tools, "MAX_ROWS", 2)
    for _ in range(3):
        TaskFactory(team=team, created_by=leader)

    found = result(leader, team, "list_tasks")

    assert (found["total"], len(found["tasks"])) == (3, 2)


def test_a_long_description_is_cut_down(team, leader, monkeypatch):
    monkeypatch.setattr(tools, "MAX_TEXT", 5)
    TaskFactory(team=team, created_by=leader, description="x" * 50)

    assert result(leader, team, "list_tasks")["tasks"][0]["description"] == "xxxxx"


# get_task


def test_get_task_returns_comments_oldest_first(team, leader, tasks):
    task = tasks["mine"]
    CommentFactory(task=task, author=leader, body="First")
    CommentFactory(task=task, author=leader, body="Second")

    found = result(leader, team, "get_task", task_id=task.pk)

    assert found["title"] == "Mine"
    assert [comment["body"] for comment in found["comments"]] == ["First", "Second"]


def test_get_task_returns_the_whole_description(team, leader, monkeypatch):
    monkeypatch.setattr(tools, "MAX_TEXT", 5)
    task = TaskFactory(team=team, created_by=leader, description="x" * 50)

    assert result(leader, team, "get_task", task_id=task.pk)["description"] == "x" * 50


def test_get_task_keeps_the_newest_comments_when_there_are_too_many(
    team, leader, tasks, monkeypatch
):
    monkeypatch.setattr(tools, "MAX_ROWS", 2)
    for body in ("One", "Two", "Three"):
        CommentFactory(task=tasks["mine"], author=leader, body=body)

    found = result(leader, team, "get_task", task_id=tasks["mine"].pk)

    assert [comment["body"] for comment in found["comments"]] == ["Two", "Three"]


def test_a_member_cannot_read_a_teammates_task(team, member, tasks):
    assert refusal(member, team, "get_task", task_id=tasks["theirs"].pk)


def test_get_task_stays_on_the_team_being_asked_about(team, leader):
    other = MembershipFactory(user=leader, role=TeamMembership.Role.LEADER).team
    elsewhere = TaskFactory(team=other, created_by=leader)

    assert refusal(leader, team, "get_task", task_id=elsewhere.pk)


def test_get_task_cannot_reach_a_stranger_team(team, leader):
    assert refusal(leader, team, "get_task", task_id=TaskFactory().pk)


@pytest.mark.parametrize("task_id", ["abc", "1; DROP TABLE", None, [], {}, 1.5, 2**70, -1])
def test_get_task_survives_a_bad_id(team, leader, task_id):
    assert refusal(leader, team, "get_task", task_id=task_id)


def test_get_task_needs_an_id(team, leader):
    assert "task_id" in refusal(leader, team, "get_task")


# get_stats


def test_a_member_gets_only_their_own_stats(team, member, tasks):
    stats = result(member, team, "get_stats")

    assert (stats["scope"], stats["members"]) == ("self", [])


def test_a_leader_gets_every_members_stats_by_name_and_no_email(team, leader, member, tasks):
    member.first_name, member.last_name = "Sara", "Ali"
    member.save()

    text = call(leader, team, "get_stats")["result"][0]["text"]

    assert "Sara Ali" in text
    assert "@" not in text
    assert json.loads(text)["scope"] == "team"


def test_get_stats_takes_a_period(team, leader):
    stats = result(leader, team, "get_stats", start="2026-01-01", end="2026-01-31")

    assert (stats["start"], stats["end"]) == ("2026-01-01", "2026-01-31")


def test_get_stats_refuses_a_backwards_period(team, leader):
    assert "start" in refusal(leader, team, "get_stats", start="2026-02-01", end="2026-01-01")


def test_get_stats_refuses_a_date_that_is_not_one(team, leader):
    assert "start" in refusal(leader, team, "get_stats", start="soon")


@pytest.mark.parametrize(
    ("start", "end"), [("0001-01-01", "0001-01-02"), ("9999-12-30", "9999-12-31")]
)
def test_get_stats_survives_the_ends_of_the_calendar(team, leader, start, end):
    assert call(leader, team, "get_stats", start=start, end=end)["call_id"] == "c1"


# recent_messages


def test_recent_messages_read_oldest_first_by_name(team, member):
    member.first_name = "Sara"
    member.save()
    MessageFactory(team=team, author=member, body="Morning")
    MessageFactory(team=team, author=member, body="Lunch?")

    messages = result(member, team, "recent_messages")["messages"]

    assert [message["body"] for message in messages] == ["Morning", "Lunch?"]
    assert messages[0]["author"] == "Sara"


def test_recent_messages_keep_to_the_team_and_the_newest(team, member, monkeypatch):
    monkeypatch.setattr(tools, "MAX_ROWS", 1)
    MessageFactory(body="Elsewhere")
    MessageFactory(team=team, author=member, body="Old")
    MessageFactory(team=team, author=member, body="New")

    assert [m["body"] for m in result(member, team, "recent_messages")["messages"]] == ["New"]


# Someone who left the team while the model was working


def test_a_stranger_gets_nothing_from_the_task_list(team, leader, tasks, outsider):
    assert result(outsider, team, "list_tasks")["total"] == 0


@pytest.mark.parametrize("name", ["get_stats", "recent_messages"])
def test_a_stranger_is_refused(team, outsider, name):
    assert refusal(outsider, team, name)


def test_a_stranger_cannot_read_a_task(team, tasks, outsider):
    assert refusal(outsider, team, "get_task", task_id=tasks["mine"].pk)


# Formatting


def test_names_fall_back_to_a_label_with_no_email():
    user = UserFactory.build(pk=7, email="private@example.com")

    assert tools.display_name(user) == "User 7"


def test_times_read_in_the_teams_timezone(team, leader):
    team.timezone = "Asia/Tokyo"
    team.save()
    TaskFactory(team=team, created_by=leader, due_at=datetime(2026, 1, 1, 20, 0, tzinfo=UTC))

    assert result(leader, team, "list_tasks")["tasks"][0]["due"] == "2026-01-02 05:00"
