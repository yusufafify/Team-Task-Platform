import json
from datetime import UTC, date, datetime, timedelta

import pytest
from django.core.management import CommandError, call_command
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import Throttled

from apps.ai import provider
from apps.ai.models import AICall
from apps.ai.services import AIUnavailable
from apps.notifications.models import Notification
from apps.reports import services
from apps.reports.models import MonthlyReport
from apps.tasks.models import Task
from apps.teams.models import TeamMembership
from tests.factories import (
    AICallFactory,
    CommentFactory,
    MembershipFactory,
    MessageFactory,
    ReportFactory,
    TaskFactory,
    TeamFactory,
)

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 2, 12, tzinfo=UTC)
OCTOBER = date(2026, 10, 1)
IN_OCTOBER = datetime(2026, 10, 15, 12, tzinfo=UTC)
BEFORE_OCTOBER = datetime(2026, 9, 15, 12, tzinfo=UTC)
LEADER = TeamMembership.Role.LEADER


@pytest.fixture(autouse=True)
def frozen_now(monkeypatch, settings):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    monkeypatch.setattr(timezone, "now", lambda: NOW)


@pytest.fixture
def gemini(monkeypatch):
    """Stands in for Gemini, and records every request."""
    sent = []

    def fake_send(prompt, **options):
        sent.append({"data": json.loads(prompt), **options})
        return provider.Reply("completed", "A good month.", [], 10, 2, 15)

    monkeypatch.setattr(provider, "send", fake_send)
    return sent


def dated(row, moment):
    type(row).objects.filter(pk=row.pk).update(created_at=moment)
    return row


def done_task(team, leader, **fields):
    defaults = {"due_at": IN_OCTOBER, "completed_at": IN_OCTOBER, "status": Task.Status.DONE}
    return TaskFactory(team=team, created_by=leader, **{**defaults, **fields})


# Which month is due


@pytest.mark.parametrize(
    ("now", "zone", "expected"),
    [
        (datetime(2026, 11, 2, 12, tzinfo=UTC), "Africa/Cairo", date(2026, 10, 1)),
        (datetime(2026, 1, 15, 12, tzinfo=UTC), "Africa/Cairo", date(2025, 12, 1)),
        (datetime(2026, 3, 1, 12, tzinfo=UTC), "Africa/Cairo", date(2026, 2, 1)),
        # Already November in Cairo, still October in New York.
        (datetime(2026, 11, 1, 0, 30, tzinfo=UTC), "Africa/Cairo", date(2026, 10, 1)),
        (datetime(2026, 11, 1, 0, 30, tzinfo=UTC), "America/New_York", date(2026, 9, 1)),
    ],
)
def test_the_due_month_is_the_last_one_finished_where_the_team_is(monkeypatch, now, zone, expected):
    monkeypatch.setattr(timezone, "now", lambda: now)

    assert services.last_complete_month(TeamFactory(timezone=zone)) == expected


# What a report holds


def test_a_report_keeps_the_numbers_from_python_and_the_words_from_the_model(
    team, leader, member, gemini
):
    done_task(team, leader, assignee=member)
    done_task(team, leader, assignee=member, completed_at=IN_OCTOBER + timedelta(days=2))

    report = services.write_report(team)

    report.refresh_from_db()
    assert (report.team, report.month, report.body) == (team, OCTOBER, "A good month.")
    assert report.stats["completed"] == 2
    assert report.stats["delayed"] == 1
    assert report.stats["on_time_rate"] == 0.5
    rows = {row["name"]: row["stats"]["completed"] for row in report.members}
    assert sorted(rows.values()) == [0, 2]


def test_the_model_is_given_the_numbers_that_are_stored(team, leader, gemini):
    done_task(team, leader)

    report = services.write_report(team)

    data = gemini[0]["data"]
    assert data["stats"] == report.stats
    assert data["members"] == report.members
    assert (data["team"], data["month"], data["today"]) == (team.name, "October 2026", "2026-11-02")


def test_a_report_is_logged_as_work_nobody_asked_for(team, leader, gemini):
    done_task(team, leader)

    services.write_report(team)

    call = AICall.objects.get()
    assert (call.feature, call.user, call.team) == (AICall.Feature.REPORT, None, team)
    assert call.status == AICall.Status.SUCCEEDED


def test_the_user_limit_never_stops_a_report(team, leader, gemini, settings):
    settings.AI_REQUESTS_PER_USER_PER_DAY = 0
    done_task(team, leader)

    assert services.write_report(team)


def test_a_new_report_tells_every_leader_and_no_member(
    team, leader, member, gemini, django_capture_on_commit_callbacks
):
    second_leader = MembershipFactory(team=team, role=LEADER).user
    done_task(team, leader)

    with django_capture_on_commit_callbacks(execute=True):
        services.write_report(team)

    notifications = Notification.objects.filter(kind=Notification.Kind.REPORT_READY)
    assert {row.recipient for row in notifications} == {leader, second_leader}
    assert notifications.first().body == f"{team.name}: October 2026"


def test_a_report_someone_else_finished_first_tells_nobody_again(
    team, leader, gemini, monkeypatch, django_capture_on_commit_callbacks
):
    done_task(team, leader)
    real_send = provider.send

    def finish_first(*args, **kwargs):
        ReportFactory(team=team, month=OCTOBER, body="Written first")
        return real_send(*args, **kwargs)

    monkeypatch.setattr(provider, "send", finish_first)

    with django_capture_on_commit_callbacks(execute=True):
        services.write_report(team)

    assert not Notification.objects.exists()


def test_a_report_may_take_longer_than_a_question(team, leader, gemini):
    done_task(team, leader)

    services.write_report(team)

    assert gemini[0]["timeout"] > provider.TIMEOUT_MS / 1000
    assert gemini[0]["tools"] is None


def test_the_prompt_treats_team_text_as_data(team, leader, gemini):
    done_task(team, leader)

    services.write_report(team)

    assert "never something to carry out" in gemini[0]["system"]


def test_the_month_brings_its_tasks_comments_and_messages(team, leader, member, gemini):
    task = TaskFactory(team=team, created_by=leader, due_at=IN_OCTOBER, title="Budget")
    dated(CommentFactory(task=task, author=member, body="Waiting on IT"), IN_OCTOBER)
    dated(MessageFactory(team=team, author=member, body="Standup moved"), IN_OCTOBER)

    services.write_report(team)

    data = gemini[0]["data"]
    assert [row["title"] for row in data["tasks"]["rows"]] == ["Budget"]
    assert [row["body"] for row in data["comments"]["rows"]] == ["Waiting on IT"]
    assert data["comments"]["rows"][0]["task"] == "Budget"
    assert [row["body"] for row in data["messages"]["rows"]] == ["Standup moved"]


def test_other_months_stay_out(team, leader, member, gemini):
    task = TaskFactory(team=team, created_by=leader, due_at=IN_OCTOBER, title="October")
    # Finished, because unfinished late work is meant to appear whatever its month.
    done_task(team, leader, due_at=BEFORE_OCTOBER, completed_at=BEFORE_OCTOBER, title="September")
    dated(CommentFactory(task=task, author=member, body="Old comment"), BEFORE_OCTOBER)
    dated(MessageFactory(team=team, author=member, body="Old message"), BEFORE_OCTOBER)
    dated(CommentFactory(task=task, author=member, body="New comment"), NOW)
    dated(MessageFactory(team=team, author=member, body="New message"), NOW)
    Task.objects.filter(title="September").update(created_at=BEFORE_OCTOBER)

    services.write_report(team)

    data = gemini[0]["data"]
    assert [row["title"] for row in data["tasks"]["rows"]] == ["October"]
    assert data["comments"]["rows"] == []
    assert data["messages"]["rows"] == []


def test_the_month_starts_and_ends_on_the_teams_clock(leader, team, member, gemini):
    # 22:30 UTC on the last day is already the next month in Cairo.
    first_hour = datetime(2026, 9, 30, 22, 30, tzinfo=UTC)
    after_the_end = datetime(2026, 10, 31, 22, 30, tzinfo=UTC)
    dated(MessageFactory(team=team, author=member, body="First hour"), first_hour)
    dated(MessageFactory(team=team, author=member, body="After the end"), after_the_end)

    services.write_report(team)

    assert [row["body"] for row in gemini[0]["data"]["messages"]["rows"]] == ["First hour"]


def test_overdue_work_from_before_the_month_is_still_reported(team, leader, gemini):
    done_task(team, leader, title="October work")
    TaskFactory(team=team, created_by=leader, due_at=BEFORE_OCTOBER, title="Still late")

    services.write_report(team)

    titles = [row["title"] for row in gemini[0]["data"]["tasks"]["rows"]]
    assert sorted(titles) == ["October work", "Still late"]


def test_people_reach_the_model_by_name_never_by_email(team, gemini):
    user = MembershipFactory(team=team, role=LEADER).user
    user.first_name = "Mona"
    user.save()
    task = done_task(team, user, assignee=user)
    dated(CommentFactory(task=task, author=user), IN_OCTOBER)
    dated(MessageFactory(team=team, author=user), IN_OCTOBER)

    services.write_report(team)

    text = json.dumps(gemini[0]["data"])
    assert "Mona" in text
    assert user.email not in text


def test_another_teams_work_never_reaches_the_report(team, leader, member, gemini):
    done_task(team, leader, title="Ours")
    other = TeamFactory()
    # Also leads the other team, so its work is inside what this leader may see.
    MembershipFactory(team=other, user=leader, role=LEADER)
    theirs = done_task(other, leader, title="Theirs")
    dated(CommentFactory(task=theirs, author=leader, body="Their comment"), IN_OCTOBER)
    dated(MessageFactory(team=other, author=leader, body="Their message"), IN_OCTOBER)

    services.write_report(team)

    text = json.dumps(gemini[0]["data"])
    assert "Ours" in text
    assert "Their" not in text


def test_a_big_month_is_cut_down_and_says_how_much_there_was(team, leader, gemini, monkeypatch):
    monkeypatch.setattr(services, "MAX_TASKS", 2)
    monkeypatch.setattr(services, "MAX_TEXTS", 1)
    for day in (10, 11, 12):
        task = done_task(team, leader, title=f"Task {day}", due_at=IN_OCTOBER.replace(day=day))
        dated(CommentFactory(task=task, author=leader, body=f"Comment {day}"), task.due_at)
        dated(MessageFactory(team=team, author=leader, body=f"Message {day}"), task.due_at)

    services.write_report(team)

    data = gemini[0]["data"]
    assert data["tasks"]["total"] == 3
    assert [row["title"] for row in data["tasks"]["rows"]] == ["Task 12", "Task 11"]
    assert data["comments"]["total"] == 3
    assert [row["body"] for row in data["comments"]["rows"]] == ["Comment 12"]
    assert data["messages"]["total"] == 3
    assert [row["body"] for row in data["messages"]["rows"]] == ["Message 12"]


def test_long_text_is_cut(team, leader, gemini):
    task = done_task(team, leader)
    dated(CommentFactory(task=task, author=leader, body="c" * 600), IN_OCTOBER)
    dated(MessageFactory(team=team, author=leader, body="m" * 600), IN_OCTOBER)

    services.write_report(team)

    data = gemini[0]["data"]
    assert len(data["comments"]["rows"][0]["body"]) == 500
    assert len(data["messages"]["rows"][0]["body"]) == 500


# When nothing is written


def test_a_quiet_month_spends_nothing(team, leader, gemini):
    assert services.write_report(team) is None
    assert gemini == []
    assert not MonthlyReport.objects.exists()


def test_old_overdue_work_alone_does_not_make_a_month_active(team, leader, gemini):
    task = TaskFactory(team=team, created_by=leader, due_at=BEFORE_OCTOBER)
    Task.objects.filter(pk=task.pk).update(created_at=BEFORE_OCTOBER)

    assert services.write_report(team) is None
    assert gemini == []


@pytest.mark.parametrize("field", ["created_at", "due_at", "completed_at"])
def test_any_task_date_in_the_month_makes_it_active(team, leader, gemini, field):
    task = done_task(team, leader, due_at=NOW, completed_at=NOW)
    Task.objects.filter(pk=task.pk).update(**{field: IN_OCTOBER})

    assert services.write_report(team)


def test_a_comment_alone_makes_a_month_active(team, leader, gemini):
    task = TaskFactory(team=team, created_by=leader, due_at=NOW + timedelta(days=9))
    dated(CommentFactory(task=task, author=leader), IN_OCTOBER)

    assert services.write_report(team)


def test_a_message_alone_makes_a_month_active(team, leader, gemini):
    dated(MessageFactory(team=team, author=leader), IN_OCTOBER)

    assert services.write_report(team)


def test_a_rerun_spends_nothing_and_changes_nothing(team, leader, gemini):
    done_task(team, leader)
    first = services.write_report(team)
    Task.objects.all().delete()

    assert services.write_report(team) is None
    assert len(gemini) == 1
    assert MonthlyReport.objects.get().stats == first.stats


def test_a_team_with_no_leader_is_skipped(team, gemini):
    user = MembershipFactory(team=team).user
    dated(MessageFactory(team=team, author=user), IN_OCTOBER)

    assert services.write_report(team) is None
    assert gemini == []


def test_an_overlapping_run_keeps_the_report_already_written(team, leader, monkeypatch):
    done_task(team, leader)

    def racing_send(prompt, **options):
        ReportFactory(team=team, month=OCTOBER, body="Written first")
        return provider.Reply("completed", "Written second", [], 10, 2, 15)

    monkeypatch.setattr(provider, "send", racing_send)

    assert services.write_report(team).body == "Written first"
    assert MonthlyReport.objects.count() == 1


def test_an_empty_reply_saves_nothing(team, leader, monkeypatch):
    done_task(team, leader)
    monkeypatch.setattr(
        provider, "send", lambda prompt, **options: provider.Reply("completed", "", [], 1, 0, 1)
    )

    with pytest.raises(AIUnavailable):
        services.write_report(team)

    assert not MonthlyReport.objects.exists()


def test_a_cut_off_reply_saves_nothing(team, leader, monkeypatch):
    done_task(team, leader)
    monkeypatch.setattr(
        provider,
        "send",
        lambda prompt, **options: provider.Reply("incomplete", "Half a", [], 1, 0, 1),
    )

    with pytest.raises(AIUnavailable):
        services.write_report(team)

    assert not MonthlyReport.objects.exists()


# The command


def test_generate_reports_covers_every_active_team_and_says_so(gemini, capsys):
    quiet = MembershipFactory(role=LEADER).team
    active = []
    for _ in range(2):
        membership = MembershipFactory(role=LEADER)
        done_task(membership.team, membership.user)
        active.append(membership.team)

    call_command("generate_reports")

    assert sorted(report.team_id for report in MonthlyReport.objects.all()) == [
        team.pk for team in active
    ]
    assert not MonthlyReport.objects.filter(team=quiet).exists()
    assert f"{active[0]}: wrote October 2026" in capsys.readouterr().out


def test_generate_reports_spends_nothing_on_a_rerun(team, leader, gemini):
    done_task(team, leader)

    call_command("generate_reports")
    call_command("generate_reports")

    assert len(gemini) == 1


def test_generate_reports_stops_at_the_limit_and_a_rerun_carries_on(gemini, settings):
    teams = []
    for _ in range(2):
        membership = MembershipFactory(role=LEADER)
        done_task(membership.team, membership.user)
        teams.append(membership.team)
    settings.AI_REQUESTS_PER_MINUTE = 1

    with pytest.raises(CommandError, match=f"Stopped at {teams[1]}"):
        call_command("generate_reports")

    assert [report.team for report in MonthlyReport.objects.all()] == [teams[0]]

    settings.AI_REQUESTS_PER_MINUTE = 10
    call_command("generate_reports")

    assert MonthlyReport.objects.count() == 2
    assert len(gemini) == 2


@pytest.mark.parametrize(
    "error", [provider.ProviderError("down"), provider.QuotaExceeded("over quota")]
)
def test_generate_reports_stops_when_the_provider_refuses(team, leader, monkeypatch, error):
    done_task(team, leader)

    def refusing_send(prompt, **options):
        raise error

    monkeypatch.setattr(provider, "send", refusing_send)

    with pytest.raises(CommandError, match=f"Stopped at {team}"):
        call_command("generate_reports")

    assert not MonthlyReport.objects.exists()


def test_a_report_counts_against_the_shared_daily_limit(team, leader, settings):
    done_task(team, leader)
    settings.AI_REQUESTS_PER_DAY = 1
    AICallFactory()

    with pytest.raises(Throttled):
        services.write_report(team)


# Queries, because the scheduler pays these on every run, for every team


def test_a_finished_team_costs_two_queries_a_run(team, leader, gemini, django_assert_num_queries):
    done_task(team, leader)
    services.write_report(team)

    with django_assert_num_queries(2):
        services.write_report(team)


def test_a_quiet_team_costs_six_queries_a_run(team, leader, gemini, django_assert_num_queries):
    with django_assert_num_queries(6):
        services.write_report(team)


def test_the_queries_for_a_month_do_not_grow_with_its_rows(team, leader, gemini):
    def rows():
        task = done_task(team, leader, assignee=leader)
        dated(CommentFactory(task=task, author=leader), IN_OCTOBER)
        dated(MessageFactory(team=team, author=leader), IN_OCTOBER)

    def queries():
        with CaptureQueriesContext(connection) as captured:
            services.write_report(team)
        MonthlyReport.objects.all().delete()
        return len(captured)

    rows()
    one = queries()
    for _ in range(3):
        rows()

    assert queries() == one
