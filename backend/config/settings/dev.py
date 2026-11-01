"""Local development settings. Each value can be overridden from .env."""

from .base import *
from .base import env

DEBUG = env.bool("DJANGO_DEBUG", default=True)
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-not-secret")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
# Neon's pooler is PgBouncer in transaction mode, which can't keep a server-side cursor open.
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://localhost:5432/nesma")
    | {"DISABLE_SERVER_SIDE_CURSORS": True}
}
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://localhost:8081"],
)
