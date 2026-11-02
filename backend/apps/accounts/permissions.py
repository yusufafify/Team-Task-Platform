from django.conf import settings
from rest_framework.permissions import SAFE_METHODS, BasePermission


class TrustedOrigin(BasePermission):
    """Stops cross-site request forgery, because browsers attach auth cookies by themselves.

    SameSite keeps other sites out, and this also covers sibling subdomains. Browsers always send
    Origin on a write and page scripts can't change it. Native apps send none and hold no cookies.
    """

    message = "This origin is not allowed."

    def has_permission(self, request, view):
        origin = request.headers.get("Origin")
        return (
            request.method in SAFE_METHODS
            or origin is None
            or origin in settings.CORS_ALLOWED_ORIGINS
        )


class NoBrowser(BasePermission):
    """Keeps endpoints that return tokens in the body away from any page script."""

    message = "This endpoint is only for the mobile app."

    def has_permission(self, request, view):
        return "Origin" not in request.headers
