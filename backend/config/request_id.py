"""Gives every request an ID, so a client's report can be matched to its log lines."""

import logging
from collections.abc import Callable
from contextvars import ContextVar
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

current_request_id: ContextVar[str] = ContextVar("current_request_id", default="-")


class RequestIdMiddleware:
    """Always makes its own ID, because a client's value would reach the logs unchecked."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.request_id = uuid4().hex
        # Never reset: Django logs 4xx and 5xx responses after this method returns.
        current_request_id.set(request.request_id)
        response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        return response


class RequestIdFilter(logging.Filter):
    """Lets a log format use `%(request_id)s`."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id.get()
        return True
