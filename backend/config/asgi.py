"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from django.conf import settings
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

if settings.SCHEDULER_IN_SERVER:
    from daphne.server import twisted_loop

    from config import scheduler

    # On Daphne's own loop, because Daphne has no ASGI lifespan, and a job started from a plain
    # thread would run `push()` on a second loop, against queues only this loop may touch.
    # Kept in a variable, because the loop holds its tasks only weakly.
    scheduler_task = twisted_loop.create_task(scheduler.run_forever())
