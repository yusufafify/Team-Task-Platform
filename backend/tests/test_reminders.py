"""Due-soon and overdue reminders: one per due date, to the assignee, whenever a run gets there."""

from datetime import timedelta

import pytest
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.notifications.models import Notification
from apps.notifications.services import remind
from apps.tasks.models import Task
from apps.tasks.services import send_reminders, update_task
from apps.teams.services import remove_member
from tests.factories import MembershipFactory, TaskFactory

pytestmark = pytest.mark.django_db

DUE_SOON = Notification.Kind.TASK_DUE_SOON
OVERDUE = Notification.Kind.TASK_OVERDUE


@pytest.fixture
def due(team, leader, member):
    def task_due_in(hours, **fields):
        moment = timezone.now() + timedelta(hours=hours)
        defaults = {"team": team, "created_by": leader, "assignee": member, "due_at": moment}
        return TaskFactory(**{**defaults, **fields})

    return task_due_in


def kinds():
    return sorted(Notification.objects.values_list("kind", flat=True))


def test_a_task_due_within_a_day_reminds_its_assignee(due, member):
    task = due(23, title="Ship the build")

    send_reminders()

    reminder = Notification.objects.get()
    assert (reminder.recipient, reminder.task, reminder.kind) == (member, task, DUE_SOON)
    assert reminder.body == "Ship the build"
    assert reminder.title


def test_an_overdue_task_reminds_its_assignee(due, member):
    task = due(-1)

    send_reminders()

    reminder = Notification.objects.get()
    assert (reminder.recipient, reminder.task, reminder.kind) == (member, task, OVERDUE)


def test_a_task_due_later_stays_quiet(due):
    due(25)

    send_reminders()

    assert kinds() == []


@pytest.mark.parametrize("hours", [23, -1])
def test_finished_work_stays_quiet(due, hours):
    due(hours, status=Task.Status.DONE, completed_at=timezone.now())

    send_reminders()

    assert kinds() == []


@pytest.mark.parametrize("hours", [23, -1])
def test_unassigned_work_has_nobody_to_remind(due, hours):
    due(hours, assignee=None)

    send_reminders()

    assert kinds() == []


def test_a_deactivated_assignee_is_not_reminded(due, member):
    member.is_active = False
    member.save()
    due(23)

    send_reminders()

    assert kinds() == []


def test_someone_removed_from_the_team_is_not_reminded(team, leader, member, due):
    due(23)

    remove_member(leader, team.pk, member.pk)
    send_reminders()

    assert kinds() == []


def test_a_reminder_reaches_only_the_assignee(due, team, member):
    MembershipFactory(team=team)
    due(23)

    send_reminders()

    assert Notification.objects.get().recipient == member


def test_a_second_run_sends_nothing(due):
    due(23)
    due(-1)

    send_reminders()
    send_reminders()

    assert kinds() == [DUE_SOON, OVERDUE]


def test_due_soon_then_overdue_are_two_reminders(due, monkeypatch):
    due(1)
    send_reminders()
    later = timezone.now() + timedelta(hours=2)
    monkeypatch.setattr(timezone, "now", lambda: later)

    send_reminders()

    assert kinds() == [DUE_SOON, OVERDUE]


def test_a_missed_run_catches_up_with_only_what_is_true_now(due, monkeypatch):
    due(1)
    later = timezone.now() + timedelta(days=3)
    monkeypatch.setattr(timezone, "now", lambda: later)

    send_reminders()

    assert kinds() == [OVERDUE]


def test_a_new_due_date_earns_a_new_reminder(due, leader):
    task = due(23)
    send_reminders()

    update_task(leader, task, due_at=timezone.now() + timedelta(hours=10))
    send_reminders()

    assert kinds() == [DUE_SOON, DUE_SOON]


def test_a_new_assignee_gets_their_own_reminder(due, team, leader):
    task = due(23)
    send_reminders()
    newcomer = MembershipFactory(team=team).user

    update_task(leader, task, assignee_id=newcomer.pk)
    send_reminders()

    assert Notification.objects.filter(kind=DUE_SOON, recipient=newcomer).count() == 1


def test_overlapping_runs_send_one_reminder(due, monkeypatch):
    task = due(23)
    sent = []
    monkeypatch.setattr("apps.notifications.services._announce", sent.append)

    remind(task, DUE_SOON, "Due soon")
    remind(task, DUE_SOON, "Due soon")

    assert len(sent) == 1
    assert Notification.objects.count() == 1


def test_the_database_refuses_a_second_reminder_for_one_due_date(due, member):
    task = due(23)
    same = {"recipient": member, "task": task, "kind": DUE_SOON, "due_at": task.due_at}
    Notification.objects.create(title="First", **same)

    with pytest.raises(IntegrityError), transaction.atomic():
        Notification.objects.create(title="Second", **same)


def test_an_ordinary_notification_can_repeat(due, member):
    task = due(100)
    assigned = Notification.Kind.TASK_ASSIGNED

    Notification.objects.create(recipient=member, task=task, kind=assigned, title="One")
    Notification.objects.create(recipient=member, task=task, kind=assigned, title="Two")

    assert Notification.objects.count() == 2


def test_the_command_sends_them(due):
    due(23)

    call_command("send_reminders")

    assert kinds() == [DUE_SOON]


def test_nothing_due_costs_two_queries(due, django_assert_num_queries):
    due(100)

    with django_assert_num_queries(2):
        send_reminders()


def test_a_task_already_reminded_costs_no_more_on_later_runs(due, django_assert_num_queries):
    due(23)
    send_reminders()

    with django_assert_num_queries(2):
        send_reminders()
