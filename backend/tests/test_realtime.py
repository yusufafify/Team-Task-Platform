import json
from datetime import timedelta
from types import SimpleNamespace

import msgpack
import pytest
from asgiref.sync import async_to_sync, sync_to_async
from channels.testing import WebsocketCommunicator
from django.db import transaction
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.authentication import ACCESS_COOKIE
from apps.chat.services import post_message
from apps.notifications import consumers
from apps.notifications.models import Notification
from apps.notifications.serializers import NotificationSerializer
from apps.notifications.services import notify
from apps.tasks.services import add_comment
from apps.teams.services import remove_member
from config.asgi import application
from tests.factories import MembershipFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db

ORIGIN = "http://localhost:5173"
EXPIRED = 4401


@pytest.fixture(autouse=True)
def keep_the_tests_connection(monkeypatch):
    """Channels drops any connection outside autocommit, which is the transaction a test runs in."""
    monkeypatch.setattr("channels.db.close_old_connections", lambda: None)


def run(start):
    """Runs on this thread's connection, so a socket sees what the test's transaction wrote."""

    async def scenario():
        await start()

    async_to_sync(scenario)()


def token_for(user, lifetime=None):
    token = AccessToken.for_user(user)
    if lifetime is not None:
        token.set_exp(lifetime=lifetime)
    return str(token)


def bearer(user):
    return [(b"authorization", f"Bearer {token_for(user)}".encode())]


def cookie(user, origin=ORIGIN):
    headers = [(b"cookie", f"{ACCESS_COOKIE}={token_for(user)}".encode())]
    return headers + ([(b"origin", origin.encode())] if origin else [])


def socket(headers=()):
    return WebsocketCommunicator(application, "/api/v1/ws/", headers=list(headers))


async def open_socket(headers):
    live = socket(headers)
    connected, _ = await live.connect()
    assert connected
    return live


async def assert_refused(headers):
    live = await open_socket(headers)
    close = await live.receive_output()
    assert (close["type"], close["code"]) == ("websocket.close", EXPIRED)


async def next_event(live):
    return json.loads(await live.receive_from())


@pytest.fixture
def committed(django_capture_on_commit_callbacks):
    """Calls something that writes, from inside a scenario, and runs its on_commit work."""

    async def call(function, *args, **kwargs):
        def in_a_commit():
            with django_capture_on_commit_callbacks(execute=True):
                return function(*args, **kwargs)

        return await sync_to_async(in_a_commit)()

    return call


# Who may connect


def test_no_credentials_are_refused_with_a_code_the_client_can_read(db):
    run(lambda: assert_refused([]))


def test_a_bad_token_is_refused(db):
    run(lambda: assert_refused([(b"authorization", b"Bearer nonsense")]))


def test_a_malformed_header_is_refused(db):
    run(lambda: assert_refused([(b"authorization", b"\xff\xfe")]))


def test_an_expired_token_is_refused(member):
    token = token_for(member, lifetime=timedelta(seconds=-1))

    run(lambda: assert_refused([(b"authorization", f"Bearer {token}".encode())]))


def test_a_deactivated_user_is_refused(member):
    member.is_active = False
    member.save()

    run(lambda: assert_refused(bearer(member)))


def test_a_cookie_from_a_trusted_page_connects(member):
    async def scenario():
        live = await open_socket(cookie(member))
        await live.disconnect()

    run(scenario)


def test_a_cookie_from_another_site_is_refused(member):
    run(lambda: assert_refused(cookie(member, origin="https://evil.example")))


def test_a_cookie_with_no_origin_is_refused(member):
    run(lambda: assert_refused(cookie(member, origin=None)))


def test_a_bearer_token_connects_from_any_origin_because_it_cannot_be_forged(member):
    headers = [*bearer(member), (b"origin", b"https://api.example")]

    async def scenario():
        live = await open_socket(headers)
        await live.disconnect()

    run(scenario)


# Team messages


def test_a_message_reaches_the_team_as_the_rest_api_shows_it(
    api, team, leader, member, django_capture_on_commit_callbacks
):
    client = api(member)

    def post():
        with django_capture_on_commit_callbacks(execute=True):
            return client.post(f"/api/v1/teams/{team.pk}/messages/", {"body": "Morning"})

    async def scenario():
        live = await open_socket(bearer(leader))
        response = await sync_to_async(post)()

        event = await next_event(live)

        assert response.status_code == 201
        assert event == {"type": "message", "data": response.json()}
        await live.disconnect()

    run(scenario)


def test_a_message_stays_inside_its_team(team, member, outsider, committed):
    async def scenario():
        live = await open_socket(bearer(outsider))

        await committed(post_message, member, team.pk, body="Private")

        assert await live.receive_nothing()
        await live.disconnect()

    run(scenario)


def test_the_author_sees_their_own_message_on_their_other_devices(team, member, committed):
    async def scenario():
        phone, laptop = [await open_socket(bearer(member)) for _ in range(2)]

        await committed(post_message, member, team.pk, body="Hello")

        assert (await next_event(phone))["data"]["body"] == "Hello"
        assert (await next_event(laptop))["data"]["body"] == "Hello"
        await phone.disconnect()
        await laptop.disconnect()

    run(scenario)


def test_removal_stops_messages_at_once_even_on_an_open_socket(team, leader, member, committed):
    async def scenario():
        live = await open_socket(bearer(member))
        await committed(remove_member, leader, team.pk, member.pk)

        await committed(post_message, leader, team.pk, body="After you left")

        assert await live.receive_nothing()
        await live.disconnect()

    run(scenario)


def test_someone_who_joins_gets_messages_on_a_socket_already_open(team, leader, committed):
    newcomer = UserFactory()

    async def scenario():
        live = await open_socket(bearer(newcomer))
        await sync_to_async(MembershipFactory)(team=team, user=newcomer)

        await committed(post_message, leader, team.pk, body="Welcome")

        assert (await next_event(live))["data"]["body"] == "Welcome"
        await live.disconnect()

    run(scenario)


def test_a_rolled_back_message_is_never_sent(team, leader, member, committed):
    def post_then_fail():
        with pytest.raises(ZeroDivisionError), transaction.atomic():
            post_message(member, team.pk, body="Never happened")
            raise ZeroDivisionError

    async def scenario():
        live = await open_socket(bearer(leader))

        await committed(post_then_fail)

        assert await live.receive_nothing()
        await live.disconnect()

    run(scenario)


def test_a_failed_push_does_not_fail_the_post(
    api, team, member, monkeypatch, django_capture_on_commit_callbacks
):
    def broken(*args):
        raise ConnectionError

    monkeypatch.setattr("apps.chat.services.push", broken)

    with django_capture_on_commit_callbacks(execute=True):
        response = api(member).post(f"/api/v1/teams/{team.pk}/messages/", {"body": "Still saved"})

    assert response.status_code == 201


# Notifications


def test_a_notification_reaches_only_its_recipient(team, leader, member, outsider, committed):
    async def scenario():
        hers = await open_socket(bearer(member))
        theirs = await open_socket(bearer(outsider))

        await committed(notify, member.pk, Notification.Kind.TASK_ASSIGNED, "New task", body="Plan")

        event = await next_event(hers)
        stored = await sync_to_async(Notification.objects.get)(recipient=member)
        assert event["type"] == "notification"
        assert event["data"] == json.loads(json.dumps(NotificationSerializer(stored).data))
        assert await theirs.receive_nothing()
        await hers.disconnect()
        await theirs.disconnect()

    run(scenario)


def test_a_comment_arrives_as_a_live_notification(team, leader, member, committed):
    task = TaskFactory(team=team, created_by=leader, assignee=member, title="Fix the login")

    async def scenario():
        live = await open_socket(bearer(member))

        await committed(add_comment, leader, task.pk, body="Any news?")

        event = await next_event(live)
        assert (event["type"], event["data"]["body"]) == ("notification", "Fix the login")
        await live.disconnect()

    run(scenario)


# Moving to several server processes


def test_every_event_could_cross_a_shared_layer(
    team, member, monkeypatch, django_capture_on_commit_callbacks
):
    """A shared layer packs events with msgpack, so a Python-only value would break only then."""
    sent = []

    class RecordingLayer:
        async def group_send(self, group, event):
            sent.append(event)

    monkeypatch.setattr("apps.notifications.services.get_channel_layer", RecordingLayer)

    with django_capture_on_commit_callbacks(execute=True):
        post_message(member, team.pk, body="Hello")
        notify(member.pk, Notification.Kind.TASK_ASSIGNED, "New task")

    assert [event["kind"] for event in sent] == ["message", "notification"]
    for event in sent:
        assert msgpack.unpackb(msgpack.packb(event)) == event


# An open socket


def test_nothing_is_delivered_after_the_token_expires(team, leader, member, committed, monkeypatch):
    async def scenario():
        live = await open_socket(bearer(member))
        far_future = SimpleNamespace(time=lambda: 2**40)
        monkeypatch.setattr(consumers, "time", far_future)

        await committed(post_message, leader, team.pk, body="Too late")

        close = await live.receive_output()
        assert (close["type"], close["code"]) == ("websocket.close", EXPIRED)

    run(scenario)


def test_anything_a_client_sends_is_ignored(team, leader, member, committed):
    async def scenario():
        live = await open_socket(bearer(member))
        await live.send_to(text_data="not json")
        await live.send_to(bytes_data=b"\x00\x01")

        await committed(post_message, leader, team.pk, body="Still here")

        assert (await next_event(live))["data"]["body"] == "Still here"
        await live.disconnect()

    run(scenario)
