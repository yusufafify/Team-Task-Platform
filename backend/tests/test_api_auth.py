import pytest
from rest_framework.test import APIClient
from rest_framework.throttling import SimpleRateThrottle

from tests.factories import UserFactory

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register/"
LOGIN = "/api/v1/auth/login/"
REFRESH = "/api/v1/auth/refresh/"
LOGOUT = "/api/v1/auth/logout/"
LOGOUT_ALL = "/api/v1/auth/logout-all/"
ME = "/api/v1/auth/me/"
PASSWORD = "correct-horse-battery"


def _with_password(email):
    user = UserFactory(email=email)
    user.set_password(PASSWORD)
    user.save()
    return user


def login(client, email):
    return client.post(LOGIN, {"email": email, "password": PASSWORD}).json()


def test_a_new_user_registers_logs_in_and_reads_their_profile():
    client = APIClient()

    created = client.post(REGISTER, {"email": "Nora@Example.com", "password": PASSWORD})
    tokens = client.post(LOGIN, {"email": "nora@example.com", "password": PASSWORD})
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens.json()['access']}")

    assert created.status_code == 201
    assert "password" not in created.json()
    assert client.get(ME).json()["email"] == "nora@example.com"


def test_register_refuses_a_taken_email_in_any_case():
    _with_password("taken@example.com")

    response = APIClient().post(REGISTER, {"email": "TAKEN@example.com", "password": PASSWORD})

    assert response.status_code == 400
    assert "email" in response.json()


def test_register_refuses_a_weak_password():
    response = APIClient().post(REGISTER, {"email": "a@example.com", "password": "12345"})

    assert response.status_code == 400
    assert "password" in response.json()


def test_refresh_returns_a_working_access_token():
    _with_password("person@example.com")
    client = APIClient()
    tokens = client.post(LOGIN, {"email": "person@example.com", "password": PASSWORD}).json()

    refreshed = client.post(REFRESH, {"refresh": tokens["refresh"]}).json()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refreshed['access']}")

    assert client.get(ME).status_code == 200


def test_refresh_replaces_the_refresh_token_and_retires_the_old_one():
    _with_password("person@example.com")
    client = APIClient()
    old = login(client, "person@example.com")["refresh"]

    renewed = client.post(REFRESH, {"refresh": old}).json()["refresh"]

    assert renewed != old
    assert client.post(REFRESH, {"refresh": old}).status_code == 401
    assert client.post(REFRESH, {"refresh": renewed}).status_code == 200


def test_logout_revokes_the_refresh_token():
    _with_password("person@example.com")
    client = APIClient()
    refresh = login(client, "person@example.com")["refresh"]

    assert client.post(LOGOUT, {"refresh": refresh}).status_code == 200

    assert client.post(REFRESH, {"refresh": refresh}).status_code == 401


def test_logout_with_a_bad_token_is_refused():
    assert APIClient().post(LOGOUT, {"refresh": "nonsense"}).status_code == 401


def test_logout_all_revokes_every_session_of_that_user_only(api):
    user = _with_password("person@example.com")
    _with_password("other@example.com")
    client = APIClient()
    sessions = [login(client, user.email)["refresh"] for _ in range(2)]
    already_revoked = login(client, user.email)["refresh"]
    client.post(LOGOUT, {"refresh": already_revoked})
    someone_else = login(client, "other@example.com")["refresh"]

    assert api(user).post(LOGOUT_ALL).status_code == 204

    for refresh in sessions:
        assert client.post(REFRESH, {"refresh": refresh}).status_code == 401
    assert client.post(REFRESH, {"refresh": someone_else}).status_code == 200


def test_wrong_password_is_refused():
    _with_password("person@example.com")

    response = APIClient().post(LOGIN, {"email": "person@example.com", "password": "wrong"})

    assert response.status_code == 401


def test_a_deactivated_user_loses_access_with_a_token_still_in_hand():
    user = _with_password("person@example.com")
    client = APIClient()
    tokens = client.post(LOGIN, {"email": user.email, "password": PASSWORD}).json()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    user.is_active = False
    user.save()

    assert client.get(ME).status_code == 401


def test_profile_update_changes_the_name_but_not_the_email(api):
    user = UserFactory()

    response = api(user).patch(ME, {"first_name": "Nora", "email": "new@example.com"})

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.first_name == "Nora"
    assert user.email != "new@example.com"


def test_many_addresses_together_hit_the_account_wide_limit(monkeypatch):
    monkeypatch.setitem(SimpleRateThrottle.THROTTLE_RATES, "login_email", "3/min")
    payload = {"email": "person@example.com", "password": "wrong"}

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
    assert owner.post(LOGIN, {"email": user.email, "password": PASSWORD}).status_code == 200


def test_a_forged_forwarded_header_cannot_dodge_the_address_limit(settings):
    settings.REST_FRAMEWORK = settings.REST_FRAMEWORK | {"NUM_PROXIES": 1}
    client = APIClient()
    payload = {"email": "person@example.com", "password": "wrong"}

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
