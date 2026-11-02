import json
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.http import parse_cookie
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import Token

from apps.accounts.authentication import ACCESS_COOKIE
from apps.notifications.services import user_group

UNAUTHORIZED = 4401
JWT = JWTAuthentication()


def _token_from(headers: dict[bytes, bytes]) -> str | bytes | None:
    if authorization := headers.get(b"authorization"):
        # A page script can't set this on a socket, so it can't be forged from another site.
        return JWT.get_raw_token(authorization)
    # Browsers attach cookies by themselves, so a cookie counts only from a page we trust.
    origin = headers.get(b"origin", b"").decode("latin1")
    if origin not in settings.CORS_ALLOWED_ORIGINS:
        return None
    return parse_cookie(headers.get(b"cookie", b"").decode("latin1")).get(ACCESS_COOKIE)


@database_sync_to_async
def _authenticate(scope: dict) -> Token | None:
    raw_token = _token_from(dict(scope["headers"]))
    if raw_token is None:
        return None
    try:
        token = JWT.get_validated_token(raw_token)
        JWT.get_user(token)
    except AuthenticationFailed:
        return None
    return token


class LiveConsumer(AsyncWebsocketConsumer):
    """Pushes one person's events. It reads nothing from clients, who write through REST."""

    group = None

    async def connect(self):
        # Accepted first, because a browser hides the close code of a refused handshake.
        await self.accept()
        token = await _authenticate(self.scope)
        if token is None:
            await self.close(UNAUTHORIZED)
            return
        self.expires = token["exp"]
        self.group = user_group(token["user_id"])
        await self.channel_layer.group_add(self.group, self.channel_name)

    async def disconnect(self, code):
        if self.group:
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def deliver(self, event):
        # A socket outlives its token, and a token ends a deactivated person's access.
        if time.time() >= self.expires:
            await self.close(UNAUTHORIZED)
            return
        await self.send(text_data=json.dumps({"type": event["kind"], "data": event["data"]}))
