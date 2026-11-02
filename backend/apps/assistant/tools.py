"""The only functions the model can call.

None can change team data, so text planted in a comment can't make the model change anything. The
only thing written is `search` keeping its own vectors current. The asker and team come from the
request, so the model has no way to name another team. Each tool calls the same scoped services as
the views, and a refusal goes back to the model as a tool result.
"""

import json
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.http import Http404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import APIException, NotFound
from rest_framework.generics import get_object_or_404

from apps.assistant import retrieval
from apps.assistant.models import Embedding
from apps.chat.services import team_messages
from apps.tasks.models import Task
from apps.tasks.serializers import StatsQuerySerializer, TaskFilterSerializer
from apps.tasks.services import filter_tasks, list_comments, team_stats, visible_tasks
from apps.teams.models import Team

User = get_user_model()
MAX_ROWS = 50
MAX_TEXT = 500


class TaskIdSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()


class SearchSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=500)


def display_name(user: User) -> str:
    """Never an email: the model doesn't need one, and the free tier warns against personal data."""
    return user.get_full_name() or f"User {user.pk}"


def _local(moment: datetime | None, zone: ZoneInfo) -> str | None:
    return moment.astimezone(zone).strftime("%Y-%m-%d %H:%M") if moment else None


def task_row(task: Task, zone: ZoneInfo) -> dict:
    return {
        "id": task.pk,
        "title": task.title,
        "description": task.description[:MAX_TEXT],
        "status": task.status,
        "priority": task.priority,
        "assignee": display_name(task.assignee) if task.assignee else None,
        "due": _local(task.due_at, zone),
        "completed": _local(task.completed_at, zone),
        "overdue": task.status != Task.Status.DONE and task.due_at < timezone.now(),
    }


def stats_row(stats: dict) -> dict:
    """`team_stats` with its users reduced to names."""
    members = [
        {"name": display_name(row["user"]), "stats": row["stats"]} for row in stats["members"]
    ]
    return {**stats, "members": members}


def _valid(serializer_class: type[serializers.Serializer], arguments: Any) -> dict:
    serializer = serializer_class(data=arguments)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def list_tasks(user: User, team: Team, arguments: Any) -> dict:
    # `team` comes last, so a value the model invented can't replace it.
    filters = {**_valid(TaskFilterSerializer, arguments), "team": team.pk}
    tasks = filter_tasks(visible_tasks(user), **filters).select_related("assignee")
    zone = ZoneInfo(team.timezone)
    return {
        "total": tasks.count(),
        "tasks": [task_row(task, zone) for task in tasks.order_by("due_at", "id")[:MAX_ROWS]],
    }


def get_task(user: User, team: Team, arguments: Any) -> dict:
    tasks = visible_tasks(user).filter(team=team).select_related("assignee")
    task = get_object_or_404(tasks, pk=_valid(TaskIdSerializer, arguments)["task_id"])
    zone = ZoneInfo(team.timezone)
    newest = list(list_comments(user, task.pk).reverse()[:MAX_ROWS])
    return {
        **task_row(task, zone),
        "description": task.description,
        "comments": [
            {
                "author": display_name(comment.author),
                "sent": _local(comment.created_at, zone),
                "body": comment.body[:MAX_TEXT],
            }
            for comment in reversed(newest)
        ],
    }


def get_stats(user: User, team: Team, arguments: Any) -> dict:
    return stats_row(team_stats(user, team.pk, **_valid(StatsQuerySerializer, arguments)))


def recent_messages(user: User, team: Team, arguments: Any) -> dict:
    newest = list(team_messages(user, team.pk).order_by("-created_at", "-id")[:MAX_ROWS])
    zone = ZoneInfo(team.timezone)
    return {
        "messages": [
            {
                "author": display_name(message.author),
                "sent": _local(message.created_at, zone),
                "body": message.body[:MAX_TEXT],
            }
            for message in reversed(newest)
        ]
    }


def _search_row(hit: Embedding, zone: ZoneInfo) -> dict:
    if hit.task:
        return {"kind": "task", **task_row(hit.task, zone)}
    source = hit.comment or hit.message
    row = {
        "kind": "comment" if hit.comment else "message",
        "author": display_name(source.author),
        "sent": _local(source.created_at, zone),
        "body": source.body[:MAX_TEXT],
    }
    if hit.comment:
        row["task"] = {"id": hit.comment.task_id, "title": hit.comment.task.title}
    return row


def search(user: User, team: Team, arguments: Any) -> dict:
    hits = retrieval.search(user, team, _valid(SearchSerializer, arguments)["query"])
    zone = ZoneInfo(team.timezone)
    return {"results": [_search_row(hit, zone) for hit in hits]}


TOOLS = {
    "list_tasks": (
        list_tasks,
        {
            "description": (
                "List the tasks this person may see, earliest due first. Use it when the snapshot "
                f"shows only part of the list, or for done tasks. Returns at most {MAX_ROWS} rows "
                "and the total."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": Task.Status.values},
                    "priority": {"type": "string", "enum": Task.Priority.values},
                    "assignee": {
                        "type": "integer",
                        "description": "The id of a person from the snapshot's members.",
                    },
                    "overdue": {"type": "boolean", "description": "True for only overdue tasks."},
                },
            },
        },
    ),
    "get_task": (
        get_task,
        {
            "description": "Read one task in full, with its comments.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "integer"}},
                "required": ["task_id"],
            },
        },
    ),
    "get_stats": (
        get_stats,
        {
            "description": (
                "Get task stats for a period other than this month, which the snapshot has. Rates "
                "are fractions from 0 to 1. `overdue` is the count right now, whatever the period."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "description": "First day, as YYYY-MM-DD."},
                    "end": {"type": "string", "description": "Last day, as YYYY-MM-DD."},
                },
            },
        },
    ),
    "recent_messages": (
        recent_messages,
        {
            "description": (
                f"Read the latest {MAX_ROWS} messages in the team chat, oldest first. The snapshot "
                "has no chat."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    ),
    "search": (
        search,
        {
            "description": (
                "Search tasks, comments and team chat by meaning, including done tasks and old "
                "chat the other tools can't reach. Use it for what was said, decided or reported "
                "about a subject, when you don't know which task holds it. Returns the "
                f"{retrieval.MAX_RESULTS} closest matches, best first. Some may be unrelated, so "
                "ignore those. It covers only what this person may see, so when nothing fits, say "
                "you found nothing, never that nobody said it or that it doesn't exist."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A short phrase describing what to find.",
                    }
                },
                "required": ["query"],
            },
        },
    ),
}
DECLARATIONS = [{"type": "function", "name": name, **spec} for name, (_, spec) in TOOLS.items()]


def run(user: User, team: Team, call: dict) -> dict:
    """Answer one `function_call` step with a `function_result` step."""
    name = call.get("name")
    try:
        if name not in TOOLS:
            raise NotFound(f"There is no tool called {name}.")
        tool = TOOLS[name][0]
        output, is_error = tool(user, team, call.get("arguments") or {}), False
    except (APIException, Http404) as exc:
        # Http404 too: it isn't an APIException, and services raise both.
        output, is_error = {"error": getattr(exc, "detail", "Not found.")}, True
    text = json.dumps(output, default=str, ensure_ascii=False)
    return {
        "type": "function_result",
        "call_id": call["id"],
        "name": name,
        "is_error": is_error,
        "result": [{"type": "text", "text": text}],
    }
