"""Test settings. pytest builds a temporary database on the Neon test branch."""

from django.core.exceptions import ImproperlyConfigured

from .dev import *
from .dev import DATABASES, REST_FRAMEWORK, env

test_database = env.db("TEST_DATABASE_URL")
app_host = DATABASES["default"]["HOST"].replace("-pooler", "")
# Dev's default DATABASE_URL names no real database, so only a value someone set can collide.
if "DATABASE_URL" in env and test_database["HOST"].replace("-pooler", "") == app_host:
    raise ImproperlyConfigured("TEST_DATABASE_URL must not share an endpoint with DATABASE_URL.")
# pytest creates and drops its database here, which a pooler's open connections block.
if "-pooler" in test_database["HOST"]:
    raise ImproperlyConfigured("TEST_DATABASE_URL must use the direct host, not -pooler.")
DATABASES = {"default": test_database}
REST_FRAMEWORK = REST_FRAMEWORK | {"TEST_REQUEST_DEFAULT_FORMAT": "json"}
# The real hasher is slow by design, and every login test would pay for it.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
