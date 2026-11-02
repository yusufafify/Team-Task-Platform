import pytest
from django.utils import timezone

from apps.tasks.models import Task
from apps.teams.models import Team, TeamMembership
from tests.factories import MembershipFactory, TaskFactory, TeamFactory, UserFactory

pytestmark = pytest.mark.django_db

LEADER = TeamMembership.Role.LEADER
MEMBER = TeamMembership.Role.MEMBER
TEAMS = "/api/v1/teams/"


def team_url(team):
    return f"{TEAMS}{team.pk}/"


def members_url(team):
    return f"{TEAMS}{team.pk}/members/"


def member_url(team, user):
    return f"{TEAMS}{team.pk}/members/{user.pk}/"


def test_creating_a_team_makes_the_requester_its_leader(api):
    user = UserFactory()

    response = api(user).post(TEAMS, {"name": "Ops", "timezone": "Asia/Dubai"})

    assert response.status_code == 201
    assert response.json()["role"] == LEADER
    assert TeamMembership.objects.get(team_id=response.json()["id"], user=user).role == LEADER


def test_team_rejects_an_unknown_timezone(api):
    response = api(UserFactory()).post(TEAMS, {"name": "Ops", "timezone": "Mars/Olympus"})

    assert response.status_code == 400
    assert "timezone" in response.json()


def test_team_list_shows_only_the_requesters_teams_with_their_own_role(
    api, team, leader, member, outsider
):
    response = api(member).get(TEAMS)

    assert [(row["id"], row["role"]) for row in response.json()["results"]] == [(team.pk, MEMBER)]


def test_a_team_is_invisible_to_outsiders(api, team, leader, outsider):
    assert api(outsider).get(team_url(team)).status_code == 404
    assert api(outsider).patch(team_url(team), {"name": "Mine"}).status_code == 404
    assert api(outsider).delete(team_url(team)).status_code == 404


def test_only_a_leader_edits_a_team(api, team, leader, member):
    assert api(member).patch(team_url(team), {"name": "Nope"}).status_code == 403

    response = api(leader).patch(team_url(team), {"name": "Renamed"})

    assert response.json()["name"] == "Renamed"
    assert response.json()["role"] == LEADER


def test_only_a_leader_deletes_an_empty_team(api, team, leader, member):
    assert api(member).delete(team_url(team)).status_code == 403
    assert api(leader).delete(team_url(team)).status_code == 204
    assert not Team.objects.filter(pk=team.pk).exists()


def test_a_team_with_tasks_cannot_be_deleted(api, team, leader):
    TaskFactory(team=team)

    assert api(leader).delete(team_url(team)).status_code == 400
    assert Team.objects.filter(pk=team.pk).exists()


def test_members_see_the_roster_and_outsiders_do_not(api, team, leader, member, outsider):
    response = api(member).get(members_url(team))

    assert {row["user"]["id"] for row in response.json()} == {leader.pk, member.pk}
    assert api(outsider).get(members_url(team)).status_code == 404


def test_an_impossibly_large_team_id_is_a_404(api, member):
    assert api(member).get(f"{TEAMS}{10**30}/members/").status_code == 404


def test_a_leader_adds_a_user_by_email_in_any_case(api, team, leader):
    user = UserFactory(email="new@example.com")

    response = api(leader).post(members_url(team), {"email": "NEW@example.com"})

    assert response.status_code == 201
    assert team.memberships.get(user=user).role == MEMBER


def test_adding_an_unknown_or_existing_user_is_refused(api, team, leader, member):
    client = api(leader)

    assert client.post(members_url(team), {"email": "ghost@example.com"}).status_code == 400
    assert client.post(members_url(team), {"email": member.email}).status_code == 400


def test_only_leaders_of_this_team_add_members(api, team, leader, member, outsider):
    user = UserFactory()

    assert api(member).post(members_url(team), {"email": user.email}).status_code == 403
    assert api(outsider).post(members_url(team), {"email": user.email}).status_code == 404


def test_a_leader_changes_a_role(api, team, leader, member):
    response = api(leader).patch(member_url(team, member), {"role": LEADER})

    assert response.status_code == 200
    assert team.memberships.get(user=member).role == LEADER


def test_a_role_change_needs_a_valid_role(api, team, leader, member):
    client = api(leader)

    assert client.patch(member_url(team, member), {"role": "owner"}).status_code == 400
    assert client.patch(member_url(team, member), {}).status_code == 400


def test_the_last_leader_cannot_step_down_or_be_removed(api, team, leader):
    client = api(leader)

    assert client.patch(member_url(team, leader), {"role": MEMBER}).status_code == 400
    assert client.delete(member_url(team, leader)).status_code == 400
    assert team.memberships.get(user=leader).role == LEADER


def test_a_leader_steps_down_when_another_leader_remains(api, team, leader):
    MembershipFactory(team=team, role=LEADER)

    assert api(leader).patch(member_url(team, leader), {"role": MEMBER}).status_code == 200


def test_only_leaders_of_this_team_manage_members(api, team, leader, member, outsider):
    assert api(member).patch(member_url(team, leader), {"role": MEMBER}).status_code == 403
    assert api(member).delete(member_url(team, leader)).status_code == 403
    assert api(outsider).patch(member_url(team, member), {"role": LEADER}).status_code == 404
    assert api(outsider).delete(member_url(team, member)).status_code == 404


def test_a_member_of_another_team_is_a_404_here(api, team, leader, outsider):
    assert api(leader).delete(member_url(team, outsider)).status_code == 404


def test_removing_a_member_frees_open_tasks_and_keeps_finished_ones(api, team, leader, member):
    open_task = TaskFactory(team=team, assignee=member)
    done_task = TaskFactory(
        team=team, assignee=member, status=Task.Status.DONE, completed_at=timezone.now()
    )
    other_team_task = TaskFactory(team=TeamFactory(), assignee=member)

    assert api(leader).delete(member_url(team, member)).status_code == 204

    assert not team.memberships.filter(user=member).exists()
    open_task.refresh_from_db()
    done_task.refresh_from_db()
    other_team_task.refresh_from_db()
    assert open_task.assignee is None
    assert done_task.assignee == member
    assert other_team_task.assignee == member
