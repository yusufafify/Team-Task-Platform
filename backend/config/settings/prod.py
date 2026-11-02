"""Production settings. Required variables have no default, so a missing one stops startup."""

from .base import *
from .base import REST_FRAMEWORK, env

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
# No CONN_MAX_AGE: Django's docs say to leave connections unpersisted under ASGI.
# Neon's pooler is PgBouncer in transaction mode, which can't keep a server-side cursor open.
DATABASES = {"default": env.db("DATABASE_URL") | {"DISABLE_SERVER_SIDE_CURSORS": True}}
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
GEMINI_API_KEY = env("GEMINI_API_KEY")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
# Host health probes usually speak plain HTTP and would read a redirect as a failure.
SECURE_REDIRECT_EXEMPT = [r"^healthz$", r"^readyz$"]
# shortcut: assumes a TLS proxy that overwrites this header, revisit once the host is chosen.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Unset, DRF keys its throttles on the raw X-Forwarded-For, which a client can vary at will.
REST_FRAMEWORK = REST_FRAMEWORK | {"NUM_PROXIES": env.int("DJANGO_NUM_PROXIES")}
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Django's default console handler only runs with DEBUG on, which would hide prod errors.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "config.request_id.RequestIdFilter"}},
    "formatters": {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s [%(request_id)s] %(message)s"}
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "plain",
        }
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
}
