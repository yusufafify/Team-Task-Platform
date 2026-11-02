from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.response import Response
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """Keeps every API error in the shapes promised by `docs/api/overview.md`."""
    if isinstance(exc, DjangoValidationError):
        # DRF leaves Django's own error unhandled, so a crafted page cursor would answer 500.
        exc = ValidationError(as_serializer_error(exc))
    response = exception_handler(exc, context)
    if response is None or not isinstance(response.data, dict):
        return response
    detail = response.data.get("detail")
    if isinstance(detail, ErrorDetail):
        # simplejwt sends its own code, and extra keys clients have no use for.
        response.data = {"detail": detail, "code": response.data.get("code", detail.code)}
    return response
