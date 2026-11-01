from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from django.utils import timezone

from apps.tasks.models import Task
from tests.factories import MembershipFactory, TaskFactory, TeamFactory

pytestmark = pytest.mark.django_db

DONE = Task.Status.DONE
JUNE = {"start": "2030-06-01", "end": "2030-06-30"}


def stats_url(team):
    return f"/api/v1/teams/{team.pk}/stats/"


def at(day, hour=12):
    return datetime(2030, 6, day, hour, tzinfo=UTC)


def finished(team, assignee, *, due, completed):
    return TaskFactory(
        team=team, assignee=assignee, due_at=due, status=DONE, completed_at=completed
    )


def test_period_metrics_follow_the_glossary(api, team, leader, member):
    finished(team, member, due=at(10), completed=at(10))
    finished(team, member, due=at(10), completed=at(12))
    finished(team, member, due=at(10), completed=at(14))
    TaskFactory(team=team, assignee=member, due_at=at(20))

    stats = api(leader).get(stats_url(team), JUNE).json()["stats"]

    assert (stats["due"], stats["completed"]) == (4, 3)
    assert (stats["on_time"], stats["delayed"]) == (1, 2)
    assert stats["completion_rate"] == 0.75
    assert stats["on_time_rate"] == pytest.approx(1 / 3)
    assert stats["average_delay_days"] == 3


def test_tasks_outside_the_period_do_not_count(api, team, leader):
    finished(team, None, due=at(10) - timedelta(days=60), completed=at(10) - timedelta(days=60))

    stats = api(leader).get(stats_url(team), JUNE).json()["stats"]

    assert (stats["due"], stats["completed"]) == (0, 0)


def test_rates_are_null_with_nothing_to_divide_by(api, team, leader):
    stats = api(leader).get(stats_url(team), JUNE).json()["stats"]

    assert stats["completion_rate"] is None
    assert stats["on_time_rate"] is None
    assert stats["average_delay_days"] is None


def test_overdue_counts_right_now_whatever_the_period(api, team, leader):
    TaskFactory(team=team, due_at=timezone.now() - timedelta(days=1))
    finished(
        team,
        None,
        due=timezone.now() - timedelta(days=1),
        completed=timezone.now(),
    )

    assert api(leader).get(stats_url(team), JUNE).json()["stats"]["overdue"] == 1


@pytest.mark.parametrize(("zone", "due"), [("UTC", 1), ("Asia/Dubai", 0)])
def test_period_days_follow_the_team_timezone(api, leader, team, zone, due):
    # 23:30 UTC on 30 June is already 1 July in Dubai.
    team.timezone = zone
    team.save()
    TaskFactory(team=team, due_at=datetime(2030, 6, 30, 23, 30, tzinfo=UTC))

    body = api(leader).get(stats_url(team), JUNE).json()

    assert body["timezone"] == zone
    assert body["stats"]["due"] == due


def test_the_end_date_includes_the_whole_day(api, leader, team):
    # 23:30 on 30 June in Cairo, which is UTC+3 in summer.
    TaskFactory(team=team, due_at=datetime(2030, 6, 30, 20, 30, tzinfo=UTC))

    assert api(leader).get(stats_url(team), JUNE).json()["stats"]["due"] == 1


def test_leaders_see_the_team_and_every_member(api, team, leader, member):
    idle = MembershipFactory(team=team).user
    finished(team, member, due=at(10), completed=at(11))

    body = api(leader).get(stats_url(team), JUNE).json()

    assert body["scope"] == "team"
    by_user = {row["user"]["id"]: row["stats"] for row in body["members"]}
    assert set(by_user) == {leader.pk, member.pk, idle.pk}
    assert by_user[member.pk]["delayed"] == 1
    assert by_user[idle.pk]["completion_rate"] is None


def test_members_see_only_their_own_numbers(api, team, member):
    teammate = MembershipFactory(team=team).user
    finished(team, member, due=at(10), completed=at(10))
    finished(team, teammate, due=at(10), completed=at(11))

    body = api(member).get(stats_url(team), JUNE).json()

    assert body["scope"] == "self"
    assert body["members"] == []
    assert (body["stats"]["completed"], body["stats"]["delayed"]) == (1, 0)


def test_stats_are_scoped_to_one_team(api, team, leader, member, outsider):
    other_team = MembershipFactory(user=member).team
    finished(other_team, member, due=at(10), completed=at(10))

    assert api(leader).get(stats_url(team), JUNE).json()["stats"]["completed"] == 0
    assert api(outsider).get(stats_url(team), JUNE).status_code == 404


def test_the_period_defaults_to_the_month_so_far(api, team, leader):
    body = api(leader).get(stats_url(team)).json()

    today = timezone.localdate(timezone=ZoneInfo(team.timezone))
    assert body["start"] == today.replace(day=1).isoformat()
    assert body["end"] == today.isoformat()


def test_an_end_date_alone_covers_that_month_so_far(api, team, leader):
    body = api(leader).get(stats_url(team), {"end": "2020-03-15"}).json()

    assert (body["start"], body["end"]) == ("2020-03-01", "2020-03-15")


@pytest.mark.parametrize(
    "query",
    [
        {"start": "2030-06-30", "end": "2030-06-01"},
        {"start": "soon"},
    ],
)
def test_a_bad_period_is_a_client_error(api, team, leader, query):
    assert api(leader).get(stats_url(team), query).status_code == 400


@pytest.mark.parametrize("zone", ["Pacific/Kiritimati", "Pacific/Pago_Pago"])
def test_the_widest_possible_period_still_answers(api, zone):
    far_team = TeamFactory(timezone=zone)
    user = MembershipFactory(team=far_team, role="leader").user

    response = api(user).get(stats_url(far_team), {"start": "0001-01-01", "end": "9999-12-31"})

    assert response.status_code == 200
