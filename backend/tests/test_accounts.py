import pytest
from django.contrib.auth import authenticate, get_user_model
from django.db import IntegrityError

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_create_user_lowercases_the_email_and_hashes_the_password():
    user = User.objects.create_user("Ada.Lovelace@Example.COM", "s3cret-pass")

    assert user.email == "ada.lovelace@example.com"
    assert user.check_password("s3cret-pass")


def test_create_user_requires_an_email():
    with pytest.raises(ValueError, match="email"):
        User.objects.create_user("", "s3cret-pass")


def test_email_is_unique_whatever_its_case():
    User.objects.create_user("ada@example.com")

    with pytest.raises(IntegrityError):
        User.objects.create_user("ADA@example.com")


def test_login_ignores_email_case():
    user = User.objects.create_user("ada@example.com", "s3cret-pass")

    assert authenticate(username="ADA@Example.com", password="s3cret-pass") == user


def test_create_superuser_can_reach_the_admin():
    user = User.objects.create_superuser("root@example.com", "s3cret-pass")

    assert user.is_staff
    assert user.is_superuser
