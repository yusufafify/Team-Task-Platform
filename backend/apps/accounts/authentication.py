from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"
ACCESS_PATH = "/api/"
# Narrower, so the long-lived token travels only on the requests that need it.
REFRESH_PATH = "/api/v1/auth/"
SAME_SITE = "Strict"


class CookieJWTAuthentication(JWTAuthentication):
    """Browsers only. Native apps send a Bearer header, handled by the parent class."""

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_COOKIE)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token


class CookieJWTScheme(OpenApiAuthenticationExtension):
    target_class = "apps.accounts.authentication.CookieJWTAuthentication"
    name = "cookieAuth"

    def get_security_definition(self, auto_schema):
        return {"type": "apiKey", "in": "cookie", "name": ACCESS_COOKIE}


def set_auth_cookies(response: Response, *, access: str, refresh: str) -> None:
    for name, value, path, lifetime in (
        (ACCESS_COOKIE, access, ACCESS_PATH, settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]),
        (REFRESH_COOKIE, refresh, REFRESH_PATH, settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]),
    ):
        response.set_cookie(
            name,
            value,
            max_age=lifetime,
            path=path,
            httponly=True,
            secure=settings.AUTH_COOKIE_SECURE,
            samesite=SAME_SITE,
        )


def clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(ACCESS_COOKIE, path=ACCESS_PATH, samesite=SAME_SITE)
    response.delete_cookie(REFRESH_COOKIE, path=REFRESH_PATH, samesite=SAME_SITE)
