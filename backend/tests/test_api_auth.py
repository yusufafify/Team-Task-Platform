import pytest
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from apps.accounts.authentication import ACCESS_COOKIE, REFRESH_COOKIE
from apps.teams.models import Team
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
LOGOUT_ALL = "/api/v1/auth/logout-all/"
ME = "/api/v1/auth/me/"
MOBILE_LOGIN = "/api/v1/auth/mobile/login/"
MOBILE_REFRESH = "/api/v1/auth/mobile/refresh/"
MOBILE_LOGOUT = "/api/v1/auth/mobile/logout/"
TEAMS = "/api/v1/teams/"
PASSWORD = "correct-horse-battery"
EMAIL = "person@example.com"
FOREIGN_ORIGIN = "https://evil.example"


def _with_password(email=EMAIL):
    user = UserFactory(email=email)
    user.set_password(PASSWORD)
    user.save()
    return user


def credentials(email=EMAIL):
    return {"email": email, "password": PASSWORD}


def logged_in(email=EMAIL):
    client = APIClient()
    client.post(LOGIN, credentials(email))
    return client


def holding_refresh_cookie(value):
    client = APIClient()
    client.cookies[REFRESH_COOKIE] = value
    return client


def mobile_tokens(email=EMAIL):
    return APIClient().post(MOBILE_LOGIN, credentials(email)).json()


def with_bearer(access):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    return client


def test_a_new_user_registers_logs_in_and_reads_their_profile():
    client = APIClient()

    created = client.post(REGISTER, {"email": "Nora@Example.com", "password": PASSWORD})
    client.post(LOGIN, credentials("nora@example.com"))

    assert created.status_code == 201
    assert "password" not in created.json()
    assert client.get(ME).json()["email"] == "nora@example.com"


def test_login_puts_both_tokens_in_http_only_cookies_and_none_in_the_body():
    user = _with_password()

    response = APIClient().post(LOGIN, credentials())

    assert response.status_code == 200
    assert response.json() == {
        "id": user.pk,
        "email": user.email,
        "first_name": "",
        "last_name": "",
    }
    access, refresh = response.cookies[ACCESS_COOKIE], response.cookies[REFRESH_COOKIE]
    for cookie in (access, refresh):
        assert cookie["httponly"] is True
        assert cookie["samesite"] == "Strict"
    assert (access["path"], access["max-age"]) == ("/api/", 900)
    assert (refresh["path"], refresh["max-age"]) == ("/api/v1/auth/", 604800)


def test_a_bad_access_cookie_is_refused():
    client = APIClient()
    client.cookies[ACCESS_COOKIE] = "nonsense"

    assert client.get(ME).status_code == 401


def test_register_refuses_a_taken_email_in_any_case():
    _with_password("taken@example.com")

    response = APIClient().post(REGISTER, {"email": "TAKEN@example.com", "password": PASSWORD})

    assert response.status_code == 400
    assert "email" in response.json()


def test_register_refuses_a_weak_password():
    response = APIClient().post(REGISTER, {"email": "a@example.com", "password": "12345"})

    assert response.status_code == 400
    assert "password" in response.json()


def test_refresh_rotates_both_cookies_and_retires_the_old_token():
    _with_password()
    client = logged_in()
    old = client.cookies[REFRESH_COOKIE].value

    response = client.post(REFRESH)

    assert response.status_code == 204
    assert response.content == b""
    assert client.cookies[REFRESH_COOKIE].value != old
    assert ACCESS_COOKIE in response.cookies
    assert client.get(ME).status_code == 200
    assert holding_refresh_cookie(old).post(REFRESH).status_code == 401


def test_refresh_without_a_cookie_is_refused():
    assert APIClient().post(REFRESH).status_code == 401


def test_a_failed_refresh_leaves_cookies_alone_so_another_tabs_session_survives():
    _with_password()
    client = logged_in()
    old = client.cookies[REFRESH_COOKIE].value
    client.post(REFRESH)

    response = holding_refresh_cookie(old).post(REFRESH)

    assert response.status_code == 401
    assert not response.cookies


def test_wrong_password_is_refused():
    _with_password()

    response = APIClient().post(LOGIN, {"email": EMAIL, "password": "wrong"})

    assert response.status_code == 401
    assert not response.cookies


def test_a_deactivated_user_loses_access_with_a_cookie_still_in_hand():
    user = _with_password()
    client = logged_in()
    user.is_active = False
    user.save()

    assert client.get(ME).status_code == 401


def test_logout_revokes_the_refresh_token_and_clears_both_cookies():
    _with_password()
    client = logged_in()
    refresh = client.cookies[REFRESH_COOKIE].value

    response = client.post(LOGOUT)

    assert response.status_code == 204
    assert response.cookies[ACCESS_COOKIE]["max-age"] == 0
    assert response.cookies[REFRESH_COOKIE]["max-age"] == 0
    assert response.cookies[REFRESH_COOKIE]["path"] == "/api/v1/auth/"
    assert holding_refresh_cookie(refresh).post(REFRESH).status_code == 401


@pytest.mark.parametrize("cookie", [None, "nonsense"])
def test_logout_succeeds_whatever_the_cookie_holds(cookie):
    client = holding_refresh_cookie(cookie) if cookie else APIClient()

    assert client.post(LOGOUT).status_code == 204


def test_logout_all_revokes_every_session_of_that_user_only():
    _with_password()
    _with_password("other@example.com")
    client = logged_in()
    web_refresh = client.cookies[REFRESH_COOKIE].value
    mobile_refresh = mobile_tokens()["refresh"]
    someone_else = mobile_tokens("other@example.com")["refresh"]

    response = client.post(LOGOUT_ALL)

    assert response.status_code == 204
    assert response.cookies[ACCESS_COOKIE]["max-age"] == 0
    assert holding_refresh_cookie(web_refresh).post(REFRESH).status_code == 401
    assert APIClient().post(MOBILE_REFRESH, {"refresh": mobile_refresh}).status_code == 401
    assert APIClient().post(MOBILE_REFRESH, {"refresh": someone_else}).status_code == 200


def test_a_foreign_site_cannot_write_with_a_users_cookies():
    _with_password()

    response = logged_in().post(TEAMS, {"name": "Ops"}, HTTP_ORIGIN=FOREIGN_ORIGIN)

    assert response.status_code == 403
    assert not Team.objects.exists()


def test_a_known_origin_can_write():
    _with_password()
    origin = settings.CORS_ALLOWED_ORIGINS[0]

    assert logged_in().post(TEAMS, {"name": "Ops"}, HTTP_ORIGIN=origin).status_code == 201


@pytest.mark.parametrize("path", [REGISTER, LOGIN, REFRESH, LOGOUT])
def test_a_foreign_site_cannot_use_the_open_auth_endpoints(path):
    assert APIClient().post(path, {}, HTTP_ORIGIN=FOREIGN_ORIGIN).status_code == 403


def test_the_mobile_app_logs_in_with_tokens_and_no_cookies():
    _with_password()

    response = APIClient().post(MOBILE_LOGIN, credentials())

    assert set(response.json()) == {"access", "refresh"}
    assert not response.cookies
    assert with_bearer(response.json()["access"]).get(ME).json()["email"] == EMAIL


def test_mobile_refresh_rotates_the_token():
    _with_password()
    old = mobile_tokens()["refresh"]

    renewed = APIClient().post(MOBILE_REFRESH, {"refresh": old}).json()

    assert renewed["refresh"] != old
    assert with_bearer(renewed["access"]).get(ME).status_code == 200
    assert APIClient().post(MOBILE_REFRESH, {"refresh": old}).status_code == 401


def test_mobile_logout_revokes_the_token():
    _with_password()
    refresh = mobile_tokens()["refresh"]

    assert APIClient().post(MOBILE_LOGOUT, {"refresh": refresh}).status_code == 200

    assert APIClient().post(MOBILE_REFRESH, {"refresh": refresh}).status_code == 401


@pytest.mark.parametrize("path", [MOBILE_LOGIN, MOBILE_REFRESH, MOBILE_LOGOUT])
def test_browsers_are_refused_on_the_mobile_endpoints_even_from_our_own_site(path):
    response = APIClient().post(path, {}, HTTP_ORIGIN=settings.CORS_ALLOWED_ORIGINS[0])

    assert response.status_code == 403


def test_a_refresh_cookie_never_buys_a_token_in_a_response_body():
    _with_password()

    response = logged_in().post(MOBILE_REFRESH)

    assert response.status_code == 400
    assert "access" not in response.json()


def test_web_and_mobile_logins_share_one_limit():
    payload = {"email": EMAIL, "password": "wrong"}
    client = APIClient()
    statuses = [client.post(path, payload).status_code for path in [LOGIN, MOBILE_LOGIN] * 3]

    assert statuses == [401] * 5 + [429]


def test_profile_update_changes_the_name_but_not_the_email(api):
    user = UserFactory()

    response = api(user).patch(ME, {"first_name": "Nora", "email": "new@example.com"})

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.first_name == "Nora"
    assert user.email != "new@example.com"


def test_many_addresses_together_hit_the_account_wide_limit(monkeypatch):
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "login_email", "3/min")
    payload = {"email": EMAIL, "password": "wrong"}

    statuses = [
        APIClient(REMOTE_ADDR=f"10.0.0.{n}").post(LOGIN, payload).status_code for n in range(4)
    ]

    assert statuses == [401] * 3 + [429]


def test_one_address_cannot_lock_the_owner_out_however_often_it_fails(monkeypatch):
    # Just above one address's own limit, so counting refused requests would trip it.
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "login_email", "6/min")
    user = _with_password("owner@example.com")
    attacker = APIClient(REMOTE_ADDR="10.0.0.1")
    statuses = [
        attacker.post(LOGIN, {"email": user.email, "password": "wrong"}).status_code
        for _ in range(8)
    ]

    owner = APIClient(REMOTE_ADDR="10.0.0.2")

    assert statuses == [401] * 5 + [429] * 3
    assert owner.post(LOGIN, credentials(user.email)).status_code == 200


def test_a_forged_forwarded_header_cannot_dodge_the_address_limit(settings):
    settings.REST_FRAMEWORK = settings.REST_FRAMEWORK | {"NUM_PROXIES": 1}
    client = APIClient()
    payload = {"email": EMAIL, "password": "wrong"}

    statuses = [
        client.post(LOGIN, payload, HTTP_X_FORWARDED_FOR=f"10.9.8.{n}, 203.0.113.7").status_code
        for n in range(6)
    ]

    assert statuses == [401] * 5 + [429]


def test_login_email_limit_ignores_case_and_padding():
    client = APIClient()
    variants = [
        "a@example.com",
        "A@EXAMPLE.COM",
        " a@example.com",
        "a@Example.com ",
        "A@example.com",
    ]
    for email in variants:
        client.post(LOGIN, {"email": email, "password": "wrong"})

    assert client.post(LOGIN, {"email": "a@example.com", "password": "x"}).status_code == 429


def test_login_stops_one_address_guessing_many_accounts():
    client = APIClient()
    statuses = [
        client.post(LOGIN, {"email": f"user{n}@example.com", "password": "wrong"}).status_code
        for n in range(21)
    ]

    assert statuses == [401] * 20 + [429]


def test_login_with_a_non_object_body_is_a_client_error():
    assert APIClient().post(LOGIN, [1, 2]).status_code == 400


def test_register_is_throttled():
    client = APIClient()
    statuses = [
        client.post(REGISTER, {"email": "bad", "password": PASSWORD}).status_code for _ in range(11)
    ]

    assert statuses == [400] * 10 + [429]
