import pytest
from django.conf import settings
from django.core.management import call_command


@pytest.mark.django_db
def test_models_and_migrations_match():
    call_command("makemigrations", check=True, dry_run=True)


def test_settings_load():
    assert settings.ROOT_URLCONF == "config.urls"
    assert settings.TIME_ZONE == "UTC"


def test_middleware_order_keeps_the_request_id_first_then_cors_and_whitenoise():
    # The ID's middleware never answers by itself, so CORS still precedes every response.
    assert settings.MIDDLEWARE[:4] == [
        "config.request_id.RequestIdMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]
