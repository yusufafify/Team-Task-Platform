from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Count, Exists, F, OuterRef, Q, QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.notifications.models import Notification
from apps.notifications.services import notify, remind
from apps.tasks.models import Comment, Task
from apps.teams.models import TeamMembership
from apps.teams.services import LEADER, get_membership, require_leader

User = get_user_model()
MEMBER_EDITABLE_FIELDS = {"status"}
EMPTY_METRICS = {"due": 0, "completed": 0, "delayed": 0, "overdue": 0, "delay": None}
DUE_SOON_WINDOW = timedelta(hours=24)


def overdue_filter() -> Q:
    return Q(due_at__lt=timezone.now()) & ~Q(status=Task.Status.DONE)


def visible_tasks(user: User) -> QuerySet[Task]:
    """Leaders see all of their teams' tasks, members only the tasks assigned to them."""
    memberships = TeamMembership.objects.filter(user=user)
    return Task.objects.filter(
        Q(team__in=memberships.filter(role=LEADER).values("team"))
        | Q(team__in=memberships.values("team"), assignee=user)
    )


def get_visible_task(user: User, task_id: int) -> Task:
    return get_object_or_404(visible_tasks(user), pk=task_id)


def filter_tasks(
    tasks: QuerySet[Task],
    *,
    team: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee: int | None = None,
    overdue: bool = False,
) -> QuerySet[Task]:
    wanted = {"team_id": team, "status": status, "priority": priority, "assignee_id": assignee}
    tasks = tasks.filter(**{field: value for field, value in wanted.items() if value is not None})
    return tasks.filter(overdue_filter()) if overdue else tasks


def _check_assignee(team_id: int, assignee_id: int | None) -> None:
    if (
        assignee_id is not None
        and not TeamMembership.objects.filter(
            team_id=team_id, user_id=assignee_id, user__is_active=True
        ).exists()
    ):
        raise ValidationError({"assignee": ["The assignee must be an active team member."]})


def _sync_completed_at(task: Task) -> None:
    if task.status != Task.Status.DONE:
        task.completed_at = None
    elif task.completed_at is None:
        task.completed_at = timezone.now()


def _notify_assignee(actor: User, task: Task) -> None:
    if task.assignee_id not in (None, actor.pk):
        notify(
            task.assignee_id,
            Notification.Kind.TASK_ASSIGNED,
            "You were assigned a task",
            body=task.title,
            task=task,
        )


def create_task(actor: User, *, team_id: int, **fields) -> Task:
    require_leader(actor, team_id)
    _check_assignee(team_id, fields.get("assignee_id"))
    task = Task(team_id=team_id, created_by=actor, **fields)
    _sync_completed_at(task)
    with transaction.atomic():
        task.save()
        _notify_assignee(actor, task)
    return task


def update_task(actor: User, task: Task, **changes) -> Task:
    membership = get_membership(actor, task.team_id)
    if membership.role != LEADER and set(changes) - MEMBER_EDITABLE_FIELDS:
        raise PermissionDenied("Members can only change a task's status.")
    if "assignee_id" in changes:
        _check_assignee(task.team_id, changes["assignee_id"])
    reassigned = changes.get("assignee_id", task.assignee_id) != task.assignee_id
    for field, value in changes.items():
        setattr(task, field, value)
    # Only the changed columns, so two people editing a task can't undo each other's work.
    update_fields = [*changes, "updated_at"]
    if "status" in changes:
        _sync_completed_at(task)
        update_fields.append("completed_at")
    with transaction.atomic():
        task.save(update_fields=update_fields)
        if reassigned:
            _notify_assignee(actor, task)
    return task


def delete_task(actor: User, task: Task) -> None:
    require_leader(actor, task.team_id)
    task.delete()


def list_comments(user: User, task_id: int) -> QuerySet[Comment]:
    task = get_visible_task(user, task_id)
    return task.comments.select_related("author").order_by("created_at", "id")


def add_comment(actor: User, task_id: int, *, body: str) -> Comment:
    task = get_visible_task(actor, task_id)
    # Former members keep their name on old tasks but stop hearing about them.
    recipients = TeamMembership.objects.filter(
        team_id=task.team_id, user_id__in=[task.assignee_id, task.created_by_id]
    ).exclude(user=actor)
    with transaction.atomic():
        comment = Comment.objects.create(task=task, author=actor, body=body)
        for user_id in recipients.values_list("user_id", flat=True):
            notify(
                user_id,
                Notification.Kind.TASK_COMMENTED,
                "New comment on a task",
                body=task.title,
                task=task,
            )
    return comment


def _reminders_owed(kind: str) -> QuerySet[Task]:
    sent = Notification.objects.filter(
        task=OuterRef("pk"), recipient=OuterRef("assignee"), kind=kind, due_at=OuterRef("due_at")
    )
    # Removing a member unassigns their open tasks, so every assignee here is on the team.
    return (
        Task.objects.exclude(status=Task.Status.DONE)
        .filter(assignee__is_active=True)
        .filter(~Exists(sent))
    )


def send_reminders() -> None:
    """Remind assignees once per due date. It selects what's owed, so a missed run catches up."""
    now = timezone.now()
    due_soon = _reminders_owed(Notification.Kind.TASK_DUE_SOON).filter(
        due_at__range=(now, now + DUE_SOON_WINDOW)
    )
    for task in due_soon:
        remind(task, Notification.Kind.TASK_DUE_SOON, "A task is due soon")
    for task in _reminders_owed(Notification.Kind.TASK_OVERDUE).filter(overdue_filter()):
        remind(task, Notification.Kind.TASK_OVERDUE, "A task is overdue")


def _metrics(lower: datetime, upper: datetime) -> dict:
    completed = Q(completed_at__range=(lower, upper))
    delayed = completed & Q(completed_at__gt=F("due_at"))
    return {
        "due": Count("id", filter=Q(due_at__range=(lower, upper))),
        "completed": Count("id", filter=completed),
        "delayed": Count("id", filter=delayed),
        "overdue": Count("id", filter=overdue_filter()),
        "delay": Avg(F("completed_at") - F("due_at"), filter=delayed),
    }


def _with_rates(row: dict) -> dict:
    due, completed, delayed, delay = row["due"], row["completed"], row["delayed"], row["delay"]
    on_time = completed - delayed
    return {
        "due": due,
        "completed": completed,
        "on_time": on_time,
        "delayed": delayed,
        "overdue": row["overdue"],
        "completion_rate": completed / due if due else None,
        "on_time_rate": on_time / completed if completed else None,
        "average_delay_days": delay.total_seconds() / 86400 if delay else None,
    }


def team_stats(
    actor: User, team_id: int, *, start: date | None = None, end: date | None = None
) -> dict:
    """Leaders get the team and every member; members get only their own numbers."""
    membership = get_membership(actor, team_id)
    team = membership.team
    zone = ZoneInfo(team.timezone)
    today = timezone.localdate(timezone=zone)
    end = end or today
    start = start or end.replace(day=1)
    if start > end:
        raise ValidationError({"start": ["The start must not be after the end."]})

    lower = datetime.combine(start, time.min, tzinfo=zone)
    upper = datetime.combine(end, time.max, tzinfo=zone)
    metrics = _metrics(lower, upper)
    tasks = Task.objects.filter(team_id=team_id)
    period = {"start": start, "end": end, "timezone": team.timezone}

    if membership.role != LEADER:
        own = tasks.filter(assignee=actor).aggregate(**metrics)
        return {**period, "scope": "self", "stats": _with_rates(own), "members": []}

    by_assignee = {
        row["assignee"]: row
        for row in tasks.filter(assignee__isnull=False).values("assignee").annotate(**metrics)
    }
    roster = team.memberships.select_related("user").order_by("joined_at", "id")
    return {
        **period,
        "scope": "team",
        "stats": _with_rates(tasks.aggregate(**metrics)),
        "members": [
            {
                "user": member.user,
                "stats": _with_rates(by_assignee.get(member.user_id, EMPTY_METRICS)),
            }
            for member in roster
        ],
    }
