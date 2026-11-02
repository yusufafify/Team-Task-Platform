"""Settings shared by every environment. Values come only from environment variables."""

import os
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Blanks copied from .env.example count as unset, so defaults and required checks still apply.
for name in [name for name, value in os.environ.items() if not value]:
    del os.environ[name]

DEBUG = False

INSTALLED_APPS = [
    # First, so `runserver` serves sockets too. Its gunicorn alternative doesn't run on Windows.
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "apps.accounts",
    "apps.teams",
    "apps.tasks",
    "apps.chat",
    "apps.notifications",
    "apps.ai",
    "apps.assistant",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    # First, so the ID exists even when another middleware fails, and `server_error` can read it.
    "config.request_id.RequestIdMiddleware",
    # CORS must precede WhiteNoise, and WhiteNoise must directly follow SecurityMiddleware.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
# In memory, so sockets work only with one server process. A second one needs a shared layer.
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    # Cookies for the web app, Bearer for the mobile app.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.CookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "apps.accounts.permissions.TrustedOrigin",
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_RATES": {
        "login_ip": "20/min",
        "login_email_address": "5/min",
        # Must stay above login_email_address, or one address could lock an account's owner out.
        "login_email": "30/min",
        "register": "10/hour",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    # A stolen refresh token dies the next time its owner's client refreshes.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}
AUTH_COOKIE_SECURE = True
CORS_ALLOW_CREDENTIALS = True

GEMINI_API_KEY = env("GEMINI_API_KEY", default=None)
# Measured 2026-11-02 on the free tier: about 1s here, 93s or more on gemini-3.8-flash.
AI_MODEL = env("AI_MODEL", default="gemini-3.5-flash-lite")
AI_REQUESTS_PER_MINUTE = env.int("AI_REQUESTS_PER_MINUTE", default=10)
AI_REQUESTS_PER_DAY = env.int("AI_REQUESTS_PER_DAY", default=200)
AI_REQUESTS_PER_USER_PER_DAY = env.int("AI_REQUESTS_PER_USER_PER_DAY", default=30)
# Chosen because one request can hold documents and a query, which gemini-embedding-001 can't.
AI_EMBEDDING_MODEL = env("AI_EMBEDDING_MODEL", default="gemini-embedding-2")
AI_EMBEDDING_REQUESTS_PER_MINUTE = env.int("AI_EMBEDDING_REQUESTS_PER_MINUTE", default=30)
AI_EMBEDDING_REQUESTS_PER_DAY = env.int("AI_EMBEDDING_REQUESTS_PER_DAY", default=500)

SEED_USER_PASSWORD = env("SEED_USER_PASSWORD", default=None)

SPECTACULAR_SETTINGS = {
    "TITLE": "Team Task Platform API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Two models have a `role`, so both need a name. `RoleEnum` is already published.
    "ENUM_NAME_OVERRIDES": {
        "RoleEnum": "apps.teams.models.TeamMembership.Role",
        "AssistantRoleEnum": "apps.assistant.models.AssistantMessage.Role",
    },
}
