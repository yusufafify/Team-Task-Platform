import pytest
from django.db import OperationalError

from apps.teams.views import TeamViewSet


class DownConnection:
    def cursor(self):
        raise OperationalError("database is down")


def test_unknown_url_answers_in_json(client):
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found."}


def test_unhandled_error_answers_in_json_without_details(api, leader, monkeypatch):
    def fail(self):
        raise RuntimeError("secret detail")

    monkeypatch.setattr(TeamViewSet, "get_queryset", fail)
    client = api(leader)
    client.raise_request_exception = False

    response = client.get("/api/v1/teams/")

    assert response.status_code == 500
    assert response.json() == {"detail": "Server error."}


def test_healthz_never_touches_the_database(client):
    # No db fixture here, so pytest-django would fail any query.
    assert client.get("/healthz").json() == {"status": "ok"}


@pytest.mark.django_db
def test_readyz_is_ok_when_the_database_answers(client):
    assert client.get("/readyz").json() == {"status": "ok"}


def test_readyz_is_503_when_the_database_is_down(client, monkeypatch):
    monkeypatch.setattr("config.views.connection", DownConnection())

    assert client.get("/readyz").status_code == 503


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/auth/me/",
        "/api/v1/auth/logout-all/",
        "/api/v1/teams/",
        "/api/v1/teams/1/members/",
        "/api/v1/teams/1/messages/",
        "/api/v1/teams/1/stats/",
        "/api/v1/tasks/",
        "/api/v1/tasks/1/comments/",
        "/api/v1/notifications/",
    ],
)
def test_endpoints_refuse_a_request_with_no_token(api, path):
    assert api().get(path).status_code == 401
