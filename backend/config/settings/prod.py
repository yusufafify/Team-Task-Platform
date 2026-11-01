"""Production settings. Required variables have no default, so a missing one stops startup."""

from .base import *
from .base import env

DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
# Reuse avoids a TLS handshake per request. Neon drops connections when it suspends, so check them.
# shortcut: WSGI only, set CONN_MAX_AGE to 0 if chat moves to ASGI, as Django's docs say.
# Neon's pooler is PgBouncer in transaction mode, which can't keep a server-side cursor open.
DATABASES = {
    "default": env.db("DATABASE_URL")
    | {"CONN_MAX_AGE": 60, "CONN_HEALTH_CHECKS": True, "DISABLE_SERVER_SIDE_CURSORS": True}
}
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
# shortcut: assumes a TLS proxy that overwrites this header, revisit once the host is chosen.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Django's default console handler only runs with DEBUG on, which would hide prod errors.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
}
