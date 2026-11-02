"""Email and push: each reaches its person once, and a provider's failure costs nothing else."""

from datetime import timedelta
from types import SimpleNamespace

import httpx
import pytest
from django.core.management import call_command
from django.db import transaction
from django.utils import timezone

from apps.notifications import services
from apps.notifications.models import DeviceToken, Notification
from apps.notifications.services import deliver, deliver_pending, notify
from tests.factories import NotificationFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db

ASSIGNED = Notification.Kind.TASK_ASSIGNED
TOKEN = "ExponentPushToken[abc123]"
OTHER_TOKEN = "ExponentPushToken[def456]"
LIMITED = 429


class Provider:
    """Stands in for `httpx.post`, answering as a healthy provider until told otherwise."""

    def __init__(self):
        self.calls = []
        self.outcomes = {}
        self.tickets = {}

    def __call__(self, url, *, json, headers, timeout):
        self.calls.append(SimpleNamespace(url=url, json=json, headers=headers, timeout=timeout))
        outcome = self.outcomes.get(url, 200)
        if isinstance(outcome, Exception):
            raise outcome
        body = {"id": "email-1"}
        if url == services.EXPO_URL:
            ok = {"status": "ok", "id": "ticket-1"}
            body = {"data": [self.tickets.get(message["to"], ok) for message in json]}
        return httpx.Response(outcome, json=body, request=httpx.Request("POST", url))

    def to(self, url):
        return [call for call in self.calls if call.url == url]

    @property
    def emails(self):
        return self.to(services.RESEND_URL)

    @property
    def pushes(self):
        return self.to(services.EXPO_URL)


@pytest.fixture
def provider(monkeypatch, settings):
    settings.RESEND_API_KEY = "test-only"
    settings.EMAIL_FROM = "Team Tasks <tasks@example.com>"
    fake = Provider()
    monkeypatch.setattr(services.httpx, "post", fake)
    return fake


def device(user, token=TOKEN):
    return DeviceToken.objects.create(user=user, token=token)


def old(notification, age=timedelta(days=2)):
    Notification.objects.filter(pk=notification.pk).update(created_at=timezone.now() - age)
    return notification


# Email


def test_an_email_is_plain_text_to_its_recipient(provider):
    task = TaskFactory()
    notification = NotificationFactory(kind=ASSIGNED, title="New task", body="Fix it", task=task)

    deliver(notification)

    call = provider.emails[0]
    assert call.json["to"] == [notification.recipient.email]
    assert call.json["from"] == "Team Tasks <tasks@example.com>"
    assert call.json["subject"] == "New task"
    assert "Fix it" in call.json["text"]
    assert "html" not in call.json


def test_an_email_carries_what_resend_requires(provider):
    notification = NotificationFactory()

    deliver(notification)

    headers = provider.emails[0].headers
    assert headers["Authorization"] == "Bearer test-only"
    assert headers["Idempotency-Key"] == f"notification/{notification.pk}"
    # Resend refuses a request with no User-Agent, with a 403 that looks like a key problem.
    assert headers["User-Agent"]


def test_a_comment_pushes_but_never_emails(provider):
    user = UserFactory()
    device(user)

    deliver(NotificationFactory(recipient=user, kind=Notification.Kind.TASK_COMMENTED))

    assert len(provider.pushes) == 1
    assert provider.emails == []


@pytest.mark.parametrize(
    "kind",
    [
        Notification.Kind.TASK_ASSIGNED,
        Notification.Kind.TASK_DUE_SOON,
        Notification.Kind.TASK_OVERDUE,
        Notification.Kind.REPORT_READY,
    ],
)
def test_everything_else_emails(provider, kind):
    deliver(NotificationFactory(kind=kind))

    assert len(provider.emails) == 1


def test_no_api_key_sends_no_email(provider, settings):
    settings.RESEND_API_KEY = None

    deliver(NotificationFactory())

    assert provider.emails == []


def test_a_demo_address_is_never_emailed_because_it_would_bounce(provider):
    deliver(NotificationFactory(recipient=UserFactory(email="mona@demo.example")))

    assert provider.emails == []


# Push


def test_a_push_reaches_each_of_the_recipients_devices_and_no_one_elses(provider):
    user = UserFactory()
    device(user)
    device(user, OTHER_TOKEN)
    device(UserFactory(), "ExponentPushToken[theirs]")
    task = TaskFactory()

    notification = NotificationFactory(recipient=user, title="New task", body="Fix it", task=task)
    deliver(notification)

    messages = provider.pushes[0].json
    assert {message["to"] for message in messages} == {TOKEN, OTHER_TOKEN}
    assert messages[0]["title"] == "New task"
    assert messages[0]["body"] == "Fix it"
    assert messages[0]["data"] == {
        "notification": notification.pk,
        "kind": ASSIGNED,
        "task": task.pk,
    }


def test_nobody_with_a_device_means_no_call_to_expo(provider):
    deliver(NotificationFactory())

    assert provider.pushes == []


def test_a_token_expo_calls_dead_is_removed_and_the_others_stay(provider):
    user = UserFactory()
    device(user)
    device(user, OTHER_TOKEN)
    provider.tickets[TOKEN] = {
        "status": "error",
        "message": "not registered",
        "details": {"error": "DeviceNotRegistered"},
    }

    deliver(NotificationFactory(recipient=user))

    assert list(DeviceToken.objects.values_list("token", flat=True)) == [OTHER_TOKEN]


def test_a_deactivated_person_gets_neither(provider):
    user = UserFactory(is_active=False)
    device(user)

    deliver(NotificationFactory(recipient=user))

    assert provider.calls == []


# Failure


def test_a_send_that_might_work_later_goes_out_on_the_next_sweep(provider):
    provider.outcomes[services.RESEND_URL] = httpx.ConnectTimeout("too slow")
    notification = NotificationFactory()

    deliver(notification)

    notification.refresh_from_db()
    assert notification.emailed_at is None

    provider.outcomes.clear()
    deliver_pending()

    notification.refresh_from_db()
    assert notification.emailed_at is not None
    assert len(provider.emails) == 2


@pytest.mark.parametrize("status", [LIMITED, 500, 503])
def test_a_rate_limit_or_a_server_error_is_retried(provider, status):
    provider.outcomes[services.RESEND_URL] = status
    notification = NotificationFactory()

    deliver(notification)

    notification.refresh_from_db()
    assert notification.emailed_at is None


@pytest.mark.parametrize("status", [400, 403, 422])
def test_a_refusal_is_not_retried_because_it_would_never_change(provider, status):
    provider.outcomes[services.RESEND_URL] = status
    notification = NotificationFactory()

    deliver(notification)
    deliver_pending()

    assert len(provider.emails) == 1


def test_a_failed_push_still_sends_the_email_and_a_retry_repeats_only_the_push(provider):
    user = UserFactory()
    device(user)
    provider.outcomes[services.EXPO_URL] = 503
    notification = NotificationFactory(recipient=user)

    deliver(notification)
    assert len(provider.emails) == 1

    provider.outcomes.clear()
    deliver_pending()

    assert len(provider.pushes) == 2
    assert len(provider.emails) == 1


def test_a_garbled_reply_stays_owed_and_does_not_stop_the_email(provider, monkeypatch):
    user = UserFactory()
    device(user)
    healthy = services.httpx.post

    def garbled(url, **kwargs):
        reply = healthy(url, **kwargs)
        if url == services.EXPO_URL:
            return httpx.Response(200, text="<html>", request=reply.request)
        return reply

    monkeypatch.setattr(services.httpx, "post", garbled)
    notification = NotificationFactory(recipient=user)

    deliver(notification)

    notification.refresh_from_db()
    assert notification.pushed_at is None
    assert notification.emailed_at is not None


def test_a_reply_with_no_tickets_stays_owed(provider, monkeypatch):
    user = UserFactory()
    device(user)
    request = httpx.Request("POST", services.EXPO_URL)
    monkeypatch.setattr(
        services.httpx, "post", lambda url, **kwargs: httpx.Response(200, json={}, request=request)
    )
    notification = NotificationFactory(recipient=user)

    services._send_once(notification, "pushed_at", services._send_push)

    notification.refresh_from_db()
    assert notification.pushed_at is None


def test_one_bad_row_does_not_stop_a_sweep(provider):
    first, second = UserFactory(), UserFactory()
    device(first)
    NotificationFactory(recipient=first)
    NotificationFactory(recipient=second)
    provider.outcomes[services.EXPO_URL] = 503

    deliver_pending()

    assert {call.json["to"][0] for call in provider.emails} == {first.email, second.email}


def test_a_channel_someone_else_claimed_is_left_alone(provider):
    now = timezone.now()
    notification = NotificationFactory(emailed_at=now, pushed_at=now)

    deliver(notification)

    assert provider.calls == []


def test_a_stale_copy_cannot_send_twice(provider):
    notification = NotificationFactory()
    stale = Notification.objects.get(pk=notification.pk)

    deliver(notification)
    deliver(stale)

    assert len(provider.emails) == 1


def test_a_sweep_leaves_what_went_out(provider):
    deliver(NotificationFactory())
    provider.calls.clear()

    deliver_pending()

    assert provider.calls == []


def test_a_sweep_gives_up_after_a_day(provider):
    old(NotificationFactory())

    deliver_pending()

    assert provider.calls == []


def test_the_command_runs_the_sweep(provider):
    NotificationFactory()

    call_command("deliver_pending")

    assert len(provider.emails) == 1


# After a commit


def test_a_committed_notification_goes_out(provider, django_capture_on_commit_callbacks):
    user = UserFactory()
    device(user)

    with django_capture_on_commit_callbacks(execute=True):
        notify(user.pk, ASSIGNED, "New task", body="Fix it")

    assert len(provider.pushes) == 1
    assert len(provider.emails) == 1
    stored = Notification.objects.get()
    assert stored.pushed_at is not None
    assert stored.emailed_at is not None


def test_a_rolled_back_notification_never_leaves(provider, django_capture_on_commit_callbacks):
    user = UserFactory()
    device(user)

    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(ZeroDivisionError), transaction.atomic():
            notify(user.pk, ASSIGNED, "New task")
            raise ZeroDivisionError

    assert provider.calls == []


def test_a_provider_outage_does_not_fail_the_write(
    api, team, leader, member, provider, django_capture_on_commit_callbacks
):
    device(member)
    outage = httpx.ConnectError("down")
    provider.outcomes = {services.RESEND_URL: outage, services.EXPO_URL: outage}
    due = timezone.now() + timedelta(days=3)
    payload = {"team": team.pk, "title": "Fix it", "assignee": member.pk, "due_at": due}

    with django_capture_on_commit_callbacks(execute=True):
        response = api(leader).post("/api/v1/tasks/", payload)

    assert response.status_code == 201
    assert Notification.objects.get().pushed_at is None


def test_sends_are_bounded_because_they_run_inside_a_request(provider):
    deliver(NotificationFactory())

    assert provider.emails[0].timeout == services.TIMEOUT_SECONDS
    assert services.TIMEOUT_SECONDS <= 5
