import pytest
from django.db import IntegrityError
from django.utils import timezone

from apps.tasks.models import Task
from tests.factories import TaskFactory

pytestmark = pytest.mark.django_db


def test_new_task_is_unassigned_todo_at_medium_priority():
    task = TaskFactory()

    assert task.status == Task.Status.TODO
    assert task.priority == Task.Priority.MEDIUM
    assert task.assignee is None
    assert task.completed_at is None


def test_done_task_keeps_its_completion_time():
    now = timezone.now()

    assert TaskFactory(status=Task.Status.DONE, completed_at=now).completed_at == now


@pytest.mark.parametrize(
    ("status", "completed_at"),
    [(Task.Status.DONE, None), (Task.Status.IN_PROGRESS, timezone.now())],
)
def test_completion_time_must_match_the_status(status, completed_at):
    with pytest.raises(IntegrityError):
        TaskFactory(status=status, completed_at=completed_at)
