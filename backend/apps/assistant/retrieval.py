"""Search by meaning, behind the assistant's `search` tool.

Writes never call Gemini. A search's one request carries its query plus whatever is new or edited,
so results include what was just written, and nothing is spent on text nobody searches (D-017).
"""

from collections import defaultdict
from typing import NamedTuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import F, Q, TextField, Value
from django.db.models.functions import MD5, Concat, Left
from pgvector.django import CosineDistance

from apps.ai.services import embed
from apps.assistant.models import Embedding
from apps.chat.models import Message
from apps.chat.services import team_messages
from apps.tasks.models import Comment, Task
from apps.tasks.services import visible_tasks
from apps.teams.models import Team

User = get_user_model()
# Gemini refuses over 100 inputs in one request, and the query takes a place.
BATCH = 50
# shortcut: only the start of a long text can be found. Split texts up if teams paste in documents.
MAX_CHARS = 2000
MAX_RESULTS = 15
# Short, because this runs inside a question's 25 seconds.
TIMEOUT_SECONDS = 8.0

# Each: the field on Embedding, its model, the path to its team, its title, and its body.
SOURCES = (
    ("task", Task, "team", F("title"), F("description")),
    ("comment", Comment, "task__team", F("task__title"), F("body")),
    ("message", Message, "team", Value("none"), F("body")),
)


class Pending(NamedTuple):
    field: str
    pk: int
    text: str
    digest: str


def _pending(team: Team) -> list[Pending]:
    """One batch of what's new or edited, newest first.

    Compared here rather than tracked on write, so admin edits and seed data can't be missed, and a
    status change, which leaves the text alone, costs nothing.
    """
    pending = []
    for field, model, team_path, title, body in SOURCES:
        # The format Gemini Embedding 2 asks for, as it has no task types.
        text = Concat(Value("title: "), title, Value(" | text: "), body, output_field=TextField())
        rows = (
            model.objects.filter(**{team_path: team})
            .annotate(text=Left(text, MAX_CHARS))
            .annotate(
                digest=MD5(
                    Concat(Value(settings.AI_EMBEDDING_MODEL), "text", output_field=TextField())
                )
            )
            .exclude(embedding__digest=F("digest"))
            .order_by("-pk")
            .values_list("pk", "text", "digest")
        )
        pending += [Pending(field, *row) for row in rows[: BATCH - len(pending)]]
    return pending


def _store(team: Team, pending: list[Pending], vectors: list[list[float]]) -> None:
    by_field = defaultdict(list)
    for item, vector in zip(pending, vectors, strict=True):
        by_field[item.field].append(
            Embedding(team=team, digest=item.digest, vector=vector, **{f"{item.field}_id": item.pk})
        )
    try:
        with transaction.atomic():
            for field, embeddings in by_field.items():
                Embedding.objects.bulk_create(
                    embeddings,
                    update_conflicts=True,
                    unique_fields=[field],
                    update_fields=["digest", "vector"],
                )
    except IntegrityError:
        # A source was deleted while the request was out. The next search redoes this batch.
        pass


def sync(team: Team) -> int:
    """Embed one batch and return its size, so a caller can repeat until it returns 0."""
    pending = _pending(team)
    if pending:
        vectors = embed([item.text for item in pending], dimensions=Embedding.DIMENSIONS, team=team)
        _store(team, pending, vectors)
    return len(pending)


def search(user: User, team: Team, query: str) -> list[Embedding]:
    """The closest things to `query` that this person may see, best first.

    Scoped through the same services as the API, and read here rather than kept on the row, so
    losing access takes effect at once. Never call this inside `transaction.atomic`, because
    `embed` must not run in one.

    shortcut: no vector index, so this ranks every row on the team. An index filters after ranking,
    which would leave a member with few results. Add HNSW with iterative scan if a team gets slow.
    """
    # First, so a stranger is refused before a request is spent.
    messages = team_messages(user, team.pk)
    tasks = visible_tasks(user).filter(team=team)
    pending = _pending(team)
    vectors = embed(
        [*(item.text for item in pending), f"task: search result | query: {query}"],
        dimensions=Embedding.DIMENSIONS,
        user=user,
        team=team,
        timeout=TIMEOUT_SECONDS,
    )
    _store(team, pending, vectors[:-1])
    return list(
        Embedding.objects.filter(
            Q(task__in=tasks) | Q(comment__task__in=tasks) | Q(message__in=messages), team=team
        )
        .select_related("task__assignee", "comment__author", "comment__task", "message__author")
        .order_by(CosineDistance("vector", vectors[-1]))[:MAX_RESULTS]
    )
