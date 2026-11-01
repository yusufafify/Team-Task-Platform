import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.teams.models import TeamMembership
from tests.factories import TeamFactory, UserFactory

pytestmark = pytest.mark.django_db


def test_team_timezone_defaults_to_cairo():
    assert TeamFactory().timezone == "Africa/Cairo"


def test_team_accepts_a_known_timezone():
    TeamFactory.build(timezone="Asia/Dubai").full_clean()


def test_team_rejects_an_unknown_timezone():
    with pytest.raises(ValidationError) as error:
        TeamFactory.build(timezone="Mars/Olympus").full_clean()

    assert "timezone" in error.value.message_dict


def test_user_joins_a_team_only_once():
    team, user = TeamFactory(), UserFactory()
    TeamMembership.objects.create(team=team, user=user)

    with pytest.raises(IntegrityError):
        TeamMembership.objects.create(team=team, user=user, role=TeamMembership.Role.LEADER)


def test_role_is_per_team():
    user = UserFactory()
    led, joined = TeamFactory(), TeamFactory()
    TeamMembership.objects.create(team=led, user=user, role=TeamMembership.Role.LEADER)
    TeamMembership.objects.create(team=joined, user=user)

    assert set(user.teams.all()) == {led, joined}
    assert joined.memberships.get(user=user).role == TeamMembership.Role.MEMBER
