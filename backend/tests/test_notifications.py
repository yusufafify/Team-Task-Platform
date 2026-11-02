import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from apps.notifications.models import DeviceToken
from tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("token", ["ExponentPushToken[abc-123]", "ExpoPushToken[abc-123]"])
def test_device_token_accepts_expo_formats(token):
    DeviceToken(user=UserFactory(), token=token).full_clean()


@pytest.mark.parametrize(
    "token",
    [
        "abc-123",
        "ExponentPushToken[]",
        "ExponentPushToken[abc",
        "ExponentPushToken[abc]\n",
        "fcm:abc",
    ],
)
def test_device_token_rejects_other_formats(token):
    with pytest.raises(ValidationError) as error:
        DeviceToken(user=UserFactory(), token=token).full_clean()

    assert "token" in error.value.message_dict


def test_device_token_is_stored_only_once():
    token = "ExponentPushToken[abc-123]"
    DeviceToken.objects.create(user=UserFactory(), token=token)

    with pytest.raises(IntegrityError):
        DeviceToken.objects.create(user=UserFactory(), token=token)
