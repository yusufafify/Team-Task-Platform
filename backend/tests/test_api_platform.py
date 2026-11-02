import base64
import logging
import re
from urllib.parse import quote

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.management import call_command
from django.db import OperationalError
from django.urls import URLResolver, get_resolver
from rest_framework.exceptions import Throttled
from rest_framework_simplejwt.tokens import AccessToken

from apps.ai.services import AIUnavailable
from apps.teams.views import TeamViewSet
from config.exceptions import api_exception_handler
from config.request_id import RequestIdFilter
from tests.factories import TaskFactory, UserFactory

# A new public route must join this list on purpose. Every other route has to refuse a stranger.
PUBLIC_ROUTES = {
    "/healthz",
    "/readyz",
    "/api/v1/auth/register/",
    "/api/v1/auth/login/",
    "/api/v1/auth/refresh/",
    "/api/v1/auth/logout/",
    "/api/v1/auth/mobile/login/",
    "/api/v1/auth/mobile/refresh/",
    "/api/v1/auth/mobile/logout/",
}


def project_routes(patterns, prefix="/"):
    """Every URL except the admin, which has its own login, with parameters filled in."""
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            if route != "/admin/":
                yield from project_routes(pattern.url_patterns, route)
        else:
            sample = re.sub(r"<[^>]+>|\(\?P<[^>]+>[^)]+\)", "1", route)
            yield sample.replace("^", "").replace("$", "")


ROUTES = set(project_routes(get_resolver().url_patterns))
# Anything under one team or task. A new route lands here by itself.
TEAM_ROUTES = sorted(route for route in ROUTES if re.search(r"/(teams|tasks)/1/", route))


class DownConnection:
    def cursor(self):
        raise OperationalError("database is down")


def test_unknown_url_answers_in_json(client):
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.json() == {"detail": "Not found.", "code": "not_found"}


def test_unhandled_error_answers_in_json_without_details(api, leader, monkeypatch):
    def fail(self):
        raise RuntimeError("secret detail")

    monkeypatch.setattr(TeamViewSet, "get_queryset", fail)
    client = api(leader)
    client.raise_request_exception = False

    response = client.get("/api/v1/teams/")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Server error.",
        "code": "server_error",
        "request_id": response["X-Request-ID"],
    }


def test_healthz_never_touches_the_database(client):
    # No db fixture here, so pytest-django would fail any query.
    assert client.get("/healthz").json() == {"status": "ok"}


@pytest.mark.django_db
def test_readyz_is_ok_when_the_database_answers(client):
    assert client.get("/readyz").json() == {"status": "ok"}


def test_readyz_is_503_when_the_database_is_down(client, monkeypatch):
    monkeypatch.setattr("config.views.connection", DownConnection())

    assert client.get("/readyz").status_code == 503


@pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
@pytest.mark.parametrize("path", sorted(ROUTES - PUBLIC_ROUTES))
def test_every_route_refuses_a_stranger_unless_listed_as_public(api, method, path):
    assert api().generic(method, path).status_code == 401


def test_route_list_reaches_nested_routes_and_names_no_stale_public_route():
    assert "/api/v1/teams/1/members/1/" in ROUTES
    assert "/api/v1/notifications/1/read/" in ROUTES
    assert PUBLIC_ROUTES <= ROUTES


def test_a_missing_token_gets_a_code(api):
    response = api().get("/api/v1/teams/")

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


def test_a_bad_token_answers_only_detail_and_code(api):
    client = api()
    client.credentials(HTTP_AUTHORIZATION="Bearer junk")

    body = client.get("/api/v1/auth/me/").json()

    assert set(body) == {"detail", "code"}
    assert body["code"] == "token_not_valid"


def test_a_deactivated_user_keeps_the_specific_code(api, member):
    token = AccessToken.for_user(member)
    member.is_active = False
    member.save(update_fields=["is_active"])
    client = api()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    response = client.get("/api/v1/auth/me/")

    assert response.status_code == 401
    assert response.json()["code"] == "user_inactive"


def test_a_stranger_to_a_team_gets_a_not_found_code(api, team, outsider):
    response = api(outsider).get(f"/api/v1/teams/{team.pk}/")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_every_team_route_hides_the_team_from_another_teams_leader(
    api, team, leader, member, outsider
):
    task = TaskFactory(team=team, assignee=member)
    # Valid for every route, so a refusal can't be mistaken for a failed validation.
    body = {
        "body": "Hi",
        "email": UserFactory().email,
        "name": "Mine",
        "question": "Hi",
        "role": "leader",
        "status": "done",
        "title": "Mine",
    }

    for route in TEAM_ROUTES:
        path = (
            route.replace("/teams/1/", f"/teams/{team.pk}/")
            .replace("/tasks/1/", f"/tasks/{task.pk}/")
            .replace("/members/1/", f"/members/{member.pk}/")
        )
        assert api(leader).get(path).status_code != 404, path
        for method in ("get", "post", "put", "patch", "delete"):
            status = getattr(api(outsider), method)(path, body).status_code
            assert status in (404, 405), (method, path, status)


def test_the_team_route_list_reaches_every_kind_of_route():
    assert "/api/v1/teams/1/members/1/" in TEAM_ROUTES
    assert "/api/v1/teams/1/reports/" in TEAM_ROUTES
    assert "/api/v1/tasks/1/comments/" in TEAM_ROUTES


def test_a_forged_host_answers_in_json(client):
    response = client.get("/healthz", headers={"Host": "evil.example"})

    assert response.status_code == 400
    assert response.json() == {"detail": "Bad request.", "code": "bad_request"}


def test_the_published_schema_matches_the_code(tmp_path):
    generated = tmp_path / "openapi.yaml"

    call_command("spectacular", "--file", str(generated), "--validate", "--fail-on-warn")

    published = settings.BASE_DIR.parent / "docs" / "api" / "openapi.yaml"
    assert generated.read_text(encoding="utf-8") == published.read_text(encoding="utf-8")


def test_a_role_refusal_gets_a_code(api, team, member):
    response = api(member).patch(f"/api/v1/teams/{team.pk}/", {"name": "New"})

    assert response.status_code == 403
    assert response.json()["code"] == "permission_denied"


def test_unreadable_json_gets_a_code(api, leader):
    response = api(leader).post("/api/v1/teams/", "{", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["code"] == "parse_error"


def test_field_errors_stay_a_plain_map_of_fields(api, leader):
    response = api(leader).post("/api/v1/teams/", {})

    assert response.status_code == 400
    assert set(response.json()) == {"name"}


def test_a_throttled_request_keeps_its_wait_and_gets_a_code():
    response = api_exception_handler(Throttled(wait=60), {})

    assert response["Retry-After"] == "60"
    assert response.data["code"] == "throttled"


def test_an_ai_outage_reaches_clients_with_its_own_code():
    response = api_exception_handler(AIUnavailable(), {})

    assert response.status_code == 503
    assert response.data["code"] == "ai_unavailable"


@pytest.mark.parametrize("position", [b"p=notadate", b"p=\x00"])
def test_a_crafted_cursor_is_a_400_not_a_crash(api, team, member, position):
    cursor = quote(base64.b64encode(position).decode())

    response = api(member).get(f"/api/v1/teams/{team.pk}/messages/?cursor={cursor}")

    assert response.status_code == 400
    assert "non_field_errors" in response.json()


def test_a_django_validation_error_keeps_its_fields():
    response = api_exception_handler(DjangoValidationError({"name": ["Too long."]}), {})

    assert response.status_code == 400
    assert response.data == {"name": ["Too long."]}


def test_each_response_gets_its_own_request_id(client):
    first = client.get("/healthz")["X-Request-ID"]
    second = client.get("/healthz")["X-Request-ID"]

    assert first != second


def test_a_client_cannot_choose_its_request_id(client):
    response = client.get("/healthz", headers={"X-Request-ID": "forged"})

    assert response["X-Request-ID"] != "forged"


def test_the_log_line_for_an_error_response_carries_its_request_id(client, caplog):
    log_filter = RequestIdFilter()
    caplog.handler.addFilter(log_filter)

    with caplog.at_level(logging.WARNING, logger="django.request"):
        response = client.get("/nope")

    caplog.handler.removeFilter(log_filter)
    assert caplog.records[-1].request_id == response["X-Request-ID"]


def test_cors_lets_only_known_origins_send_cookies(client):
    def preflight(origin):
        return client.options(
            "/api/v1/teams/", HTTP_ORIGIN=origin, HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST"
        )

    known = preflight(settings.CORS_ALLOWED_ORIGINS[0])
    foreign = preflight("https://evil.example")

    assert known["Access-Control-Allow-Credentials"] == "true"
    assert known["Access-Control-Allow-Origin"] == settings.CORS_ALLOWED_ORIGINS[0]
    assert "Access-Control-Allow-Origin" not in foreign
