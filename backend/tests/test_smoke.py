from django.conf import settings


def test_settings_load():
    assert settings.ROOT_URLCONF == "config.urls"
    assert settings.TIME_ZONE == "UTC"


def test_middleware_order_satisfies_cors_and_whitenoise():
    assert settings.MIDDLEWARE[:3] == [
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.security.SecurityMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]
