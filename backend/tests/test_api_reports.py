from datetime import date

import pytest

from apps.teams.models import TeamMembership
from apps.teams.services import change_member_role
from tests.factories import MembershipFactory, ReportFactory

pytestmark = pytest.mark.django_db


def url(team):
    return f"/api/v1/teams/{team.pk}/reports/"


def test_a_leader_reads_the_teams_reports_newest_first(api, team, leader):
    ReportFactory(team=team, month=date(2026, 9, 1))
    ReportFactory(team=team, month=date(2026, 10, 1))

    response = api(leader).get(url(team))

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [row["month"] for row in body["results"]] == ["2026-10-01", "2026-09-01"]


def test_a_report_has_its_numbers_and_its_words(api, team, leader):
    report = ReportFactory(team=team)

    result = api(leader).get(url(team)).json()["results"][0]

    assert set(result) == {"id", "month", "stats", "members", "body", "created_at"}
    assert result["body"] == report.body
    assert result["stats"]["completed"] == report.stats["completed"]
    assert result["stats"]["on_time_rate"] == report.stats["on_time_rate"]
    assert result["members"][0]["name"] == report.members[0]["name"]
    assert result["members"][0]["stats"]["due"] == report.members[0]["stats"]["due"]


def test_a_member_is_refused_because_a_report_rates_every_teammate(api, team, member):
    ReportFactory(team=team)

    response = api(member).get(url(team))

    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"


def test_a_stranger_cannot_tell_the_team_exists(api, team, outsider):
    ReportFactory(team=team)

    response = api(outsider).get(url(team))

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_a_leader_sees_no_other_teams_reports(api, team, leader, outsider):
    ReportFactory(team=outsider.teams.get(), body="Their month")

    response = api(leader).get(url(team))

    assert response.json()["results"] == []


def test_a_demoted_leader_loses_reports_at_once(api, team, leader):
    ReportFactory(team=team)
    other = MembershipFactory(team=team, role=TeamMembership.Role.LEADER).user
    change_member_role(other, team.pk, leader.pk, role=TeamMembership.Role.MEMBER)

    assert api(leader).get(url(team)).status_code == 403


def test_reports_are_read_only(api, team, leader):
    report = ReportFactory(team=team)

    assert api(leader).post(url(team), {"body": "Forged"}).status_code == 405
    assert api(leader).delete(url(team)).status_code == 405
    report.refresh_from_db()
    assert report.body != "Forged"
