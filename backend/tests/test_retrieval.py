import json

import pytest
from django.core.management import CommandError, call_command
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from rest_framework.exceptions import NotFound

from apps.ai import provider
from apps.ai.models import AICall
from apps.ai.services import AIUnavailable
from apps.assistant import retrieval, services, tools
from apps.assistant.models import Embedding
from apps.tasks.models import Task
from apps.tasks.services import update_task
from apps.teams.models import TeamMembership
from apps.teams.services import remove_member
from tests.factories import (
    CommentFactory,
    MembershipFactory,
    MessageFactory,
    TaskFactory,
    TeamFactory,
)

pytestmark = pytest.mark.django_db

SUBJECTS = ["runway", "uniforms", "fuel"]


def fake_vector(text: str, dimensions: int) -> list[float]:
    """One axis per subject, so a text is closest to the query that names its subject."""
    vector = [0.0] * dimensions
    vector[0] = 0.01  # Cosine distance has no answer for an all-zero vector.
    for axis, subject in enumerate(SUBJECTS, start=1):
        if subject in text.casefold():
            vector[axis] = 1.0
    return vector


class FakeEmbedder:
    def __init__(self):
        self.batches = []
        self.error = None

    def __call__(self, texts, *, dimensions, timeout=None):
        self.batches.append(texts)
        if self.error:
            raise self.error
        return [fake_vector(text, dimensions) for text in texts]


@pytest.fixture(autouse=True)
def limits(settings):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    settings.AI_REQUESTS_PER_USER_PER_DAY = 100
    settings.AI_EMBEDDING_REQUESTS_PER_MINUTE = 100
    settings.AI_EMBEDDING_REQUESTS_PER_DAY = 100
    return settings


@pytest.fixture(autouse=True)
def embedder(monkeypatch):
    fake = FakeEmbedder()
    monkeypatch.setattr(provider, "embed", fake)
    return fake


def documents(batch):
    """A batch's stored items, without the query, which is always last."""
    return batch[:-1]


def sources(hits):
    return [hit.task or hit.comment or hit.message for hit in hits]


def query_for(subject):
    return f"task: search result | query: {subject}"


# Keeping the index fresh


def test_one_request_carries_the_query_and_whatever_is_missing(team, leader, embedder):
    task = TaskFactory(team=team, created_by=leader, title="Runway", description="Check the lights")
    CommentFactory(task=task, author=leader, body="Vendor is late")
    MessageFactory(team=team, author=leader, body="Lunch at one")

    retrieval.search(leader, team, "runway")

    assert len(embedder.batches) == 1
    batch = embedder.batches[0]
    assert batch[-1] == query_for("runway")
    assert set(documents(batch)) == {
        "title: Runway | text: Check the lights",
        "title: Runway | text: Vendor is late",
        "title: none | text: Lunch at one",
    }
    assert Embedding.objects.filter(team=team).count() == 3


def test_a_search_with_nothing_missing_sends_only_the_query(team, leader, embedder):
    TaskFactory(team=team, created_by=leader, title="Runway")
    retrieval.search(leader, team, "runway")

    retrieval.search(leader, team, "fuel")

    assert embedder.batches[1] == [query_for("fuel")]


def test_an_edited_task_is_embedded_again(team, leader, embedder):
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    retrieval.search(leader, team, "runway")

    update_task(leader, task, title="Uniforms")
    hits = retrieval.search(leader, team, "uniforms")

    assert documents(embedder.batches[1]) == ["title: Uniforms | text: "]
    assert sources(hits) == [task]
    # Reads the row, because one row is found first whatever its vector says.
    stored = Embedding.objects.get().vector
    assert list(stored) == pytest.approx(fake_vector("uniforms", Embedding.DIMENSIONS))


def test_a_change_the_text_does_not_show_spends_nothing(team, leader, embedder):
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    retrieval.search(leader, team, "runway")

    update_task(leader, task, status=Task.Status.BLOCKED)
    retrieval.search(leader, team, "runway")

    assert documents(embedder.batches[1]) == []


def test_an_edit_outside_the_services_is_noticed_too(team, leader, embedder):
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    retrieval.search(leader, team, "runway")

    Task.objects.filter(pk=task.pk).update(title="Fuel")
    retrieval.search(leader, team, "fuel")

    assert documents(embedder.batches[1]) == ["title: Fuel | text: "]


def test_a_new_title_reaches_its_comments(team, leader, embedder):
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    CommentFactory(task=task, author=leader, body="Vendor is late")
    retrieval.search(leader, team, "runway")

    update_task(leader, task, title="Fuel")
    retrieval.search(leader, team, "fuel")

    assert "title: Fuel | text: Vendor is late" in embedder.batches[1]


def test_changing_the_embedding_model_embeds_everything_again(limits, team, leader, embedder):
    TaskFactory(team=team, created_by=leader, title="Runway")
    retrieval.search(leader, team, "runway")

    limits.AI_EMBEDDING_MODEL = "gemini-embedding-3"
    retrieval.search(leader, team, "runway")

    assert documents(embedder.batches[1]) == ["title: Runway | text: "]


def test_a_batch_is_capped_and_starts_with_the_newest(team, leader, embedder, monkeypatch):
    monkeypatch.setattr(retrieval, "BATCH", 2)
    for title in ("Oldest", "Middle", "Newest"):
        TaskFactory(team=team, created_by=leader, title=title)

    retrieval.search(leader, team, "runway")

    assert documents(embedder.batches[0]) == [
        "title: Newest | text: ",
        "title: Middle | text: ",
    ]


def test_a_batch_is_shared_across_kinds_of_source(team, leader, embedder, monkeypatch):
    monkeypatch.setattr(retrieval, "BATCH", 2)
    TaskFactory(team=team, created_by=leader, title="Runway")
    MessageFactory(team=team, author=leader, body="First")
    MessageFactory(team=team, author=leader, body="Second")

    retrieval.search(leader, team, "runway")

    assert len(documents(embedder.batches[0])) == 2


def test_long_text_is_cut_before_it_is_sent(team, leader, embedder):
    TaskFactory(team=team, created_by=leader, title="Runway", description="x" * 10_000)

    retrieval.search(leader, team, "runway")

    assert len(documents(embedder.batches[0])[0]) == retrieval.MAX_CHARS


def test_another_teams_rows_are_not_sent_or_stored(team, leader, embedder):
    other = TeamFactory()
    MessageFactory(team=other, body="Their private plan")
    MessageFactory(team=team, author=leader, body="Ours")

    retrieval.search(leader, team, "runway")

    assert documents(embedder.batches[0]) == ["title: none | text: Ours"]
    assert not Embedding.objects.filter(team=other).exists()


def test_a_failed_request_stores_nothing_and_the_next_search_retries(team, leader, embedder):
    TaskFactory(team=team, created_by=leader, title="Runway")
    embedder.error = provider.ProviderError("down")

    with pytest.raises(AIUnavailable):
        retrieval.search(leader, team, "runway")

    assert not Embedding.objects.exists()
    embedder.error = None
    assert len(retrieval.search(leader, team, "runway")) == 1


@pytest.mark.parametrize("fields", [set(), {"task", "message"}])
def test_a_vector_belongs_to_exactly_one_source(team, leader, fields):
    linked = {
        "task": TaskFactory(team=team, created_by=leader),
        "message": MessageFactory(team=team, author=leader),
    }
    vector = [0.1] * Embedding.DIMENSIONS

    with pytest.raises(IntegrityError, match="embedding_has_one_source"), transaction.atomic():
        Embedding.objects.create(
            team=team, digest="x", vector=vector, **{field: linked[field] for field in fields}
        )


def test_deleting_a_source_deletes_its_vector(team, leader):
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    CommentFactory(task=task, author=leader)
    retrieval.search(leader, team, "runway")
    assert Embedding.objects.count() == 2

    task.delete()

    assert not Embedding.objects.exists()


def test_a_source_deleted_while_the_request_was_out_loses_only_this_write(
    team, leader, embedder, monkeypatch
):
    # Django's foreign keys wait for commit, which a test's transaction never reaches.
    with connection.cursor() as cursor:
        cursor.execute("SET CONSTRAINTS ALL IMMEDIATE")
    task = TaskFactory(team=team, created_by=leader, title="Runway")
    real_embed = provider.embed

    def embed_then_delete(texts, **options):
        vectors = real_embed(texts, **options)
        Task.objects.filter(pk=task.pk).delete()
        return vectors

    monkeypatch.setattr(provider, "embed", embed_then_delete)

    assert retrieval.search(leader, team, "runway") == []
    assert not Embedding.objects.exists()


# Scoping


@pytest.fixture
def seeded(team, leader, member):
    """Everything about the runway, so only scoping decides what comes back."""
    mine = TaskFactory(team=team, created_by=leader, assignee=member, title="Runway mine")
    theirs = TaskFactory(team=team, created_by=leader, assignee=leader, title="Runway theirs")
    return {
        "mine": mine,
        "theirs": theirs,
        "my_comment": CommentFactory(task=mine, author=leader, body="Runway note"),
        "their_comment": CommentFactory(task=theirs, author=leader, body="Runway secret"),
        "chat": MessageFactory(team=team, author=leader, body="Runway chat"),
    }


def test_a_leader_finds_everything_on_the_team(team, leader, seeded):
    hits = sources(retrieval.search(leader, team, "runway"))

    assert set(hits) == set(seeded.values())


def test_a_member_finds_only_their_work_and_the_team_chat(team, member, seeded):
    hits = sources(retrieval.search(member, team, "runway"))

    assert set(hits) == {seeded["mine"], seeded["my_comment"], seeded["chat"]}


def test_a_stranger_is_refused_before_any_request_is_spent(
    team, leader, outsider, seeded, embedder
):
    retrieval.search(leader, team, "runway")
    spent = len(embedder.batches)

    with pytest.raises(NotFound):
        retrieval.search(outsider, team, "runway")

    assert len(embedder.batches) == spent


def test_nothing_crosses_from_another_team_even_when_it_matches_best(team, leader):
    other = TeamFactory()
    both = MembershipFactory(team=other, role=TeamMembership.Role.LEADER).user
    MembershipFactory(team=team, user=both, role=TeamMembership.Role.LEADER)
    theirs = TaskFactory(team=other, created_by=both, assignee=both, title="Runway")
    CommentFactory(task=theirs, author=both, body="Runway")
    MessageFactory(team=other, author=both, body="Runway")
    ours = TaskFactory(team=team, created_by=leader, title="Runway fuel uniforms")
    # Embeds the other team's rows, or there would be nothing to leak.
    assert len(retrieval.search(both, other, "runway")) == 3

    assert sources(retrieval.search(both, team, "runway")) == [ours]


def test_a_reassigned_task_leaves_a_members_search_at_once(team, leader, member, seeded):
    retrieval.search(member, team, "runway")

    update_task(leader, seeded["mine"], assignee_id=leader.pk)
    hits = sources(retrieval.search(member, team, "runway"))

    assert seeded["mine"] not in hits
    assert seeded["my_comment"] not in hits


def test_a_removed_member_can_no_longer_search(team, leader, member, seeded):
    retrieval.search(member, team, "runway")

    remove_member(leader, team.pk, member.pk)

    with pytest.raises(NotFound):
        retrieval.search(member, team, "runway")


# Ranking


def test_the_closest_match_comes_first(team, leader):
    tasks = {
        subject: TaskFactory(team=team, created_by=leader, title=subject) for subject in SUBJECTS
    }

    # Every subject, because any fixed order puts one of them first by luck.
    for subject, task in tasks.items():
        hits = sources(retrieval.search(leader, team, subject))
        assert hits[0] == task
        assert set(hits) == set(tasks.values())


def test_results_are_capped(team, leader, monkeypatch):
    monkeypatch.setattr(retrieval, "MAX_RESULTS", 2)
    for number in range(3):
        MessageFactory(team=team, author=leader, body=f"Runway {number}")

    assert len(retrieval.search(leader, team, "runway")) == 2


def test_a_member_gets_their_results_when_hidden_rows_match_better(team, leader, member):
    """Why there's no vector index: it would filter after ranking, and come back short."""
    for number in range(30):
        TaskFactory(team=team, created_by=leader, assignee=leader, title=f"Runway {number}")
    mine = TaskFactory(team=team, created_by=leader, assignee=member, title="Fuel")

    assert sources(retrieval.search(member, team, "runway")) == [mine]


# The tool


def run_search(user, team, /, **arguments):
    step = {"type": "function_call", "id": "c1", "name": "search", "arguments": arguments}
    return tools.run(user, team, step)


def rows(step):
    assert step["is_error"] is False, step
    return json.loads(step["result"][0]["text"])["results"]


def test_the_tool_describes_each_kind_of_result(team, leader, member, seeded):
    leader.first_name, leader.last_name = "Lina", "Hassan"
    leader.save()

    results = rows(run_search(member, team, query="runway"))

    by_kind = {row["kind"]: row for row in results}
    assert by_kind["task"]["id"] == seeded["mine"].pk
    assert by_kind["task"]["title"] == "Runway mine"
    assert by_kind["comment"]["task"] == {"id": seeded["mine"].pk, "title": "Runway mine"}
    assert by_kind["comment"]["author"] == "Lina Hassan"
    assert by_kind["comment"]["body"] == "Runway note"
    assert by_kind["message"]["author"] == "Lina Hassan"
    assert by_kind["message"]["body"] == "Runway chat"
    assert by_kind["message"]["sent"]


def test_the_tool_never_gives_the_model_an_email(team, leader, member, seeded):
    text = run_search(leader, team, query="runway")["result"][0]["text"]

    assert leader.email not in text
    assert member.email not in text


def test_the_tool_caps_a_long_body(team, leader):
    MessageFactory(team=team, author=leader, body="runway " * 500)

    assert len(rows(run_search(leader, team, query="runway"))[0]["body"]) == tools.MAX_TEXT


def test_the_tool_costs_the_same_queries_however_many_results(team, leader, member):
    def add_rows():
        task = TaskFactory(team=team, created_by=leader, assignee=member, title="Runway")
        CommentFactory(task=task, author=member, body="Runway")
        MessageFactory(team=team, author=member, body="Runway")

    def count_queries():
        run_search(leader, team, query="runway")  # Embeds what's new, which isn't what's measured.
        with CaptureQueriesContext(connection) as context:
            assert rows(run_search(leader, team, query="runway"))
        return len(context)

    add_rows()
    few = count_queries()
    add_rows()
    add_rows()

    assert count_queries() == few


@pytest.mark.parametrize("arguments", [{}, {"query": ""}, {"query": "x" * 501}])
def test_a_bad_query_spends_no_request(team, leader, embedder, arguments):
    assert run_search(leader, team, **arguments)["is_error"] is True
    assert embedder.batches == []


def test_the_model_cannot_point_the_tool_at_another_team(team, leader, outsider):
    MessageFactory(team=team, author=leader, body="Runway ours")
    other = TeamMembership.objects.get(user=outsider).team
    MessageFactory(team=other, author=outsider, body="Runway theirs")
    retrieval.search(outsider, other, "runway")

    results = rows(run_search(leader, team, query="runway", team=other.pk))

    assert [row["body"] for row in results] == ["Runway ours"]


@pytest.mark.parametrize("error", [provider.QuotaExceeded("429"), provider.ProviderError("down")])
def test_a_failed_search_reaches_the_model_as_a_tool_error(team, leader, embedder, error):
    embedder.error = error

    assert run_search(leader, team, query="runway")["is_error"] is True


def test_a_tool_cannot_hold_a_question_past_its_deadline(team, leader, monkeypatch):
    received = {}

    def fake_embed(texts, *, dimensions, timeout=None):
        received["timeout"] = timeout
        return [fake_vector(text, dimensions) for text in texts]

    monkeypatch.setattr(provider, "embed", fake_embed)

    run_search(leader, team, query="runway")

    assert 0 < received["timeout"] < services.DEADLINE_SECONDS


def test_the_chatbot_can_answer_from_a_search(team, leader, seeded, monkeypatch):
    def step(reply_steps, text="", status="completed"):
        return provider.Reply(status, text, reply_steps, 10, 2, 15)

    wanted = {"type": "function_call", "id": "c1", "name": "search"}
    wanted["arguments"] = {"query": "runway"}
    output = {"type": "model_output", "content": [{"type": "text", "text": "The vendor is late."}]}
    replies = [step([wanted], status="requires_action"), step([output], "The vendor is late.")]
    prompts = []

    def fake_send(prompt, **options):
        prompts.append(prompt)
        return replies.pop(0)

    monkeypatch.setattr(provider, "send", fake_send)

    turn = services.ask(leader, team.pk, "What happened with the runway?")

    assert turn.answer.body == "The vendor is late."
    assert turn.answer.cache_key == ""
    result = prompts[1][-1]
    assert result["type"] == "function_result"
    assert "Runway secret" in result["result"][0]["text"]
    features = list(AICall.objects.values_list("feature", flat=True).order_by("id"))
    assert features == [AICall.Feature.CHAT, AICall.Feature.EMBED, AICall.Feature.CHAT]


# The backfill


def test_embed_pending_catches_up_on_every_team(leader, team, embedder, monkeypatch):
    monkeypatch.setattr(retrieval, "BATCH", 2)
    other = TeamFactory()
    for number in range(3):
        MessageFactory(team=team, author=leader, body=f"Ours {number}")
    MessageFactory(team=other, body="Theirs")

    call_command("embed_pending")

    assert Embedding.objects.filter(team=team).count() == 3
    assert Embedding.objects.filter(team=other).count() == 1
    assert AICall.objects.get(team=other).user is None


def test_embed_pending_spends_nothing_when_there_is_nothing_to_do(team, leader, embedder):
    MessageFactory(team=team, author=leader, body="Ours")
    call_command("embed_pending")
    spent = len(embedder.batches)

    call_command("embed_pending")

    assert len(embedder.batches) == spent


def test_embed_pending_stops_at_the_limit_and_keeps_what_it_finished(
    limits, team, leader, monkeypatch
):
    monkeypatch.setattr(retrieval, "BATCH", 1)
    limits.AI_EMBEDDING_REQUESTS_PER_MINUTE = 1
    for number in range(2):
        MessageFactory(team=team, author=leader, body=f"Ours {number}")

    with pytest.raises(CommandError, match="Run it again"):
        call_command("embed_pending")

    assert Embedding.objects.count() == 1


@pytest.mark.parametrize("error", [provider.QuotaExceeded("429"), provider.ProviderError("down")])
def test_embed_pending_stops_when_the_provider_refuses_too(team, leader, embedder, error):
    MessageFactory(team=team, author=leader, body="Ours")
    embedder.error = error

    with pytest.raises(CommandError, match="Run it again"):
        call_command("embed_pending")
