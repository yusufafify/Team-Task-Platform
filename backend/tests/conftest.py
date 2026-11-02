import pytest
from rest_framework.test import APIClient

from apps.teams.models import TeamMembership
from tests.factories import MembershipFactory, TeamFactory


@pytest.fixture(autouse=True)
def no_real_sends(monkeypatch):
    """Expo needs no key, so a test that registers a device could otherwise reach the real one."""

    def refuse(*args, **kwargs):
        raise AssertionError("A test tried to reach a real provider.")

    monkeypatch.setattr("apps.notifications.services.httpx.post", refuse)


@pytest.fixture
def api():
    def client_for(user=None) -> APIClient:
        client = APIClient()
        if user:
            client.force_authenticate(user)
        return client

    return client_for


@pytest.fixture
def team(db):
    return TeamFactory()


@pytest.fixture
def leader(team):
    return MembershipFactory(team=team, role=TeamMembership.Role.LEADER).user


@pytest.fixture
def member(team):
    return MembershipFactory(team=team).user


@pytest.fixture
def outsider(db):
    """Leads another team, so a leak across teams shows up even for a privileged role."""
    return MembershipFactory(role=TeamMembership.Role.LEADER).user
