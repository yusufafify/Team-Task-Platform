"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

# First, because importing the consumer needs the app registry that this fills.
http_application = get_asgi_application()

from apps.notifications.consumers import LiveConsumer  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": http_application,
        "websocket": URLRouter([path("api/v1/ws/", LiveConsumer.as_asgi())]),
    }
)
