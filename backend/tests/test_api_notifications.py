import pytest
from django.utils import timezone

from apps.notifications.models import DeviceToken, Notification
from apps.notifications.services import notify
from tests.factories import NotificationFactory, UserFactory

pytestmark = pytest.mark.django_db

NOTIFICATIONS = "/api/v1/notifications/"
DEVICES = "/api/v1/device-tokens/"
TOKEN = "ExponentPushToken[abc123]"


def ids(response):
    return [row["id"] for row in response.json()["results"]]


def test_notifications_list_only_the_requesters_newest_first(api):
    user = UserFactory()
    older = NotificationFactory(recipient=user)
    newer = NotificationFactory(recipient=user)
    NotificationFactory()

    assert ids(api(user).get(NOTIFICATIONS)) == [newer.pk, older.pk]


def test_unread_filter_and_its_count(api):
    user = UserFactory()
    unread = NotificationFactory(recipient=user)
    NotificationFactory(recipient=user, read_at=timezone.now())

    response = api(user).get(NOTIFICATIONS, {"unread": "true"})

    assert ids(response) == [unread.pk]
    assert response.json()["count"] == 1


def test_marking_read_keeps_the_first_read_time(api):
    user = UserFactory()
    notification = NotificationFactory(recipient=user)
    client = api(user)
    url = f"{NOTIFICATIONS}{notification.pk}/read/"

    first = client.post(url).json()["read_at"]
    second = client.post(url).json()["read_at"]

    assert first is not None
    assert second == first


def test_another_users_notification_is_a_404(api):
    notification = NotificationFactory()

    response = api(UserFactory()).post(f"{NOTIFICATIONS}{notification.pk}/read/")

    notification.refresh_from_db()
    assert response.status_code == 404
    assert notification.read_at is None


@pytest.mark.parametrize("bad_id", ["abc", "9" * 5000])
def test_an_id_that_cannot_be_a_number_is_a_404(api, bad_id):
    assert api(UserFactory()).post(f"{NOTIFICATIONS}{bad_id}/read/").status_code == 404


def test_read_all_touches_only_the_requesters_notifications(api):
    user = UserFactory()
    mine = NotificationFactory(recipient=user)
    other = NotificationFactory()

    assert api(user).post(f"{NOTIFICATIONS}read-all/").status_code == 204

    mine.refresh_from_db()
    other.refresh_from_db()
    assert mine.read_at is not None
    assert other.read_at is None


def test_a_failed_notification_does_not_break_the_committed_change(
    monkeypatch, django_capture_on_commit_callbacks
):
    def fail(**kwargs):
        raise RuntimeError("no notification today")

    monkeypatch.setattr(Notification.objects, "create", fail)
    user = UserFactory()

    with django_capture_on_commit_callbacks(execute=True):
        notify(user.pk, Notification.Kind.TASK_ASSIGNED, "Title")


def test_a_device_registers_its_token(api):
    user = UserFactory()

    response = api(user).post(DEVICES, {"token": TOKEN})

    assert response.status_code == 201
    assert DeviceToken.objects.get().user == user


@pytest.mark.parametrize("token", ["nonsense", "ExponentPushToken[]", "ExponentPushToken[a]b"])
def test_a_malformed_token_is_refused(api, token):
    assert api(UserFactory()).post(DEVICES, {"token": token}).status_code == 400


def test_surrounding_whitespace_never_reaches_a_stored_token(api):
    api(UserFactory()).post(DEVICES, {"token": f"{TOKEN}\n"})

    assert DeviceToken.objects.get().token == TOKEN


def test_a_token_moves_to_whoever_signed_in_last(api):
    first, second = UserFactory(), UserFactory()
    api(first).post(DEVICES, {"token": TOKEN})

    assert api(second).post(DEVICES, {"token": TOKEN}).status_code == 201

    assert DeviceToken.objects.get().user == second


def test_removing_a_token_with_a_nul_byte_is_a_client_error(api):
    assert api(UserFactory()).delete(f"{DEVICES}%00/").status_code == 400


def test_a_user_removes_only_their_own_token(api):
    owner = UserFactory()
    api(owner).post(DEVICES, {"token": TOKEN})

    api(UserFactory()).delete(f"{DEVICES}{TOKEN}/")
    assert DeviceToken.objects.filter(user=owner).exists()

    assert api(owner).delete(f"{DEVICES}{TOKEN}/").status_code == 204
    assert not DeviceToken.objects.exists()
