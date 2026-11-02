import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import httpx
import pytest
from django.db import connection
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import Throttled

from apps.ai import provider
from apps.ai.models import AICall
from apps.ai.services import AIUnavailable, embed, generate
from tests.factories import AICallFactory, UserFactory

CHAT = AICall.Feature.CHAT
EMBED = AICall.Feature.EMBED
REPLY = provider.Reply(
    status="completed", text="Hello", steps=[], input_tokens=10, output_tokens=2, total_tokens=15
)
# Noon in Los Angeles, on a day with no clock change.
NOON = datetime(2026, 11, 2, 20, 0, tzinfo=UTC)
MIDNIGHT = datetime(2026, 11, 2, 8, 0, tzinfo=UTC)


@pytest.fixture
def limits(settings):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    settings.AI_REQUESTS_PER_USER_PER_DAY = 100
    settings.AI_EMBEDDING_REQUESTS_PER_MINUTE = 100
    settings.AI_EMBEDDING_REQUESTS_PER_DAY = 100
    return settings


@pytest.fixture
def embedder(monkeypatch):
    """Stands in for Gemini's embedding call, and records every batch that reached it."""
    batches = []

    def fake_embed(texts, **options):
        batches.append(texts)
        return [[0.5, 0.5] for _ in texts]

    monkeypatch.setattr(provider, "embed", fake_embed)
    return batches


@pytest.fixture
def send(monkeypatch):
    """Stands in for Gemini, and records every prompt that reached it."""
    prompts = []

    def fake_send(prompt, **options):
        prompts.append(prompt)
        return REPLY

    monkeypatch.setattr(provider, "send", fake_send)
    return prompts


@pytest.fixture
def clock(monkeypatch):
    def set_time(moment: datetime) -> None:
        monkeypatch.setattr(timezone, "now", lambda: moment)

    return set_time


def send_that(outcome):
    """A provider stub that returns a reply, or raises an exception."""

    def fake_send(prompt, **options):
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    return fake_send


# generate: logging


@pytest.mark.django_db
def test_a_call_is_logged_with_its_usage(limits, send, team, member):
    reply = generate(CHAT, "How is the team doing?", user=member, team=team)

    call = AICall.objects.get()
    assert reply is REPLY
    assert send == ["How is the team doing?"]
    assert (call.feature, call.user, call.team) == (CHAT, member, team)
    assert call.status == AICall.Status.SUCCEEDED
    assert call.model == limits.AI_MODEL
    assert (call.input_tokens, call.output_tokens, call.total_tokens) == (10, 2, 15)
    assert call.latency_ms is not None


@pytest.mark.django_db
def test_the_log_keeps_no_prompt_or_reply(limits, send):
    generate(CHAT, "the secret plan", system="the secret system prompt")

    stored = str(model_to_dict(AICall.objects.get()))
    assert "secret" not in stored
    assert REPLY.text not in stored


@pytest.mark.django_db
def test_a_tool_request_counts_as_success(limits, monkeypatch):
    asked = provider.Reply("requires_action", "", [{"type": "function_call"}], 1, 1, 2)
    monkeypatch.setattr(provider, "send", send_that(asked))

    assert generate(CHAT, "hi").steps == asked.steps
    assert AICall.objects.get().status == AICall.Status.SUCCEEDED


@pytest.mark.django_db
def test_a_provider_failure_is_logged_and_hides_its_details(limits, monkeypatch):
    monkeypatch.setattr(provider, "send", send_that(provider.ProviderError("x" * 600)))

    with pytest.raises(AIUnavailable) as caught:
        generate(CHAT, "hi")

    call = AICall.objects.get()
    assert call.status == AICall.Status.FAILED
    assert call.error == "x" * 500
    assert call.latency_ms is not None
    assert "xxx" not in str(caught.value.detail)
    assert caught.value.status_code == 503


@pytest.mark.django_db
def test_the_providers_own_quota_refusal_reads_as_throttling(limits, monkeypatch):
    monkeypatch.setattr(provider, "send", send_that(provider.QuotaExceeded("429")))

    with pytest.raises(Throttled):
        generate(CHAT, "hi")

    assert AICall.objects.get().status == AICall.Status.FAILED


@pytest.mark.django_db
@pytest.mark.parametrize("status", ["incomplete", "requires_continuation", "failed", "cancelled"])
def test_an_unfinished_reply_never_reaches_the_caller(limits, monkeypatch, status):
    cut_off = provider.Reply(status, "Half an ans", [], 10, 2, 15)
    monkeypatch.setattr(provider, "send", send_that(cut_off))

    with pytest.raises(AIUnavailable):
        generate(CHAT, "hi")

    call = AICall.objects.get()
    assert call.status == AICall.Status.FAILED
    assert status in call.error
    assert call.total_tokens == 15


# generate: limits


@pytest.mark.django_db
def test_minute_limit_stops_the_call_before_it_is_sent(limits, send):
    limits.AI_REQUESTS_PER_MINUTE = 2
    AICallFactory.create_batch(2)

    with pytest.raises(Throttled) as caught:
        generate(CHAT, "hi")

    assert caught.value.wait == 60
    assert send == []
    assert AICall.objects.count() == 2


@pytest.mark.django_db
def test_minute_limit_forgets_older_calls(limits, send, clock):
    limits.AI_REQUESTS_PER_MINUTE = 1
    clock(NOON)
    AICallFactory()
    clock(NOON + timedelta(seconds=61))

    generate(CHAT, "hi")

    assert send == ["hi"]


@pytest.mark.django_db
def test_day_limit_stops_the_call_until_midnight_pacific(limits, send, clock):
    limits.AI_REQUESTS_PER_DAY = 1
    clock(MIDNIGHT)
    AICallFactory()
    clock(NOON)

    with pytest.raises(Throttled) as caught:
        generate(CHAT, "hi")

    assert caught.value.wait == 12 * 60 * 60
    assert send == []


@pytest.mark.django_db
def test_day_limit_starts_over_at_midnight_pacific(limits, send, clock):
    limits.AI_REQUESTS_PER_DAY = 1
    clock(MIDNIGHT - timedelta(seconds=1))
    AICallFactory()
    clock(NOON)

    generate(CHAT, "hi")

    assert send == ["hi"]


@pytest.mark.django_db
def test_wait_is_right_on_a_day_with_a_clock_change(limits, send, clock):
    limits.AI_REQUESTS_PER_DAY = 1
    # 01:00 Pacific on the 25-hour day, before the clocks go back.
    moment = datetime(2026, 11, 1, 8, 0, tzinfo=UTC)
    clock(moment)
    AICallFactory()

    with pytest.raises(Throttled) as caught:
        generate(CHAT, "hi")

    assert caught.value.wait == 24 * 60 * 60


@pytest.mark.django_db
def test_a_caller_over_two_limits_is_told_the_longer_wait(limits, send, clock):
    limits.AI_REQUESTS_PER_MINUTE = 1
    limits.AI_REQUESTS_PER_DAY = 1
    clock(NOON)
    AICallFactory()

    with pytest.raises(Throttled) as caught:
        generate(CHAT, "hi")

    assert caught.value.wait == 12 * 60 * 60


@pytest.mark.django_db
def test_user_limit_stops_only_that_user(limits, send):
    limits.AI_REQUESTS_PER_USER_PER_DAY = 1
    busy, other = UserFactory(), UserFactory()
    generate(CHAT, "first", user=busy)

    with pytest.raises(Throttled):
        generate(CHAT, "second", user=busy)

    generate(CHAT, "other user", user=other)
    generate(AICall.Feature.REPORT, "no user")
    assert send == ["first", "other user", "no user"]


@pytest.mark.django_db
def test_failed_and_unfinished_calls_still_count(limits, send):
    limits.AI_REQUESTS_PER_MINUTE = 2
    AICallFactory(status=AICall.Status.FAILED)
    AICallFactory(status=AICall.Status.PENDING)

    with pytest.raises(Throttled):
        generate(CHAT, "hi")


@pytest.mark.django_db(transaction=True)
def test_concurrent_calls_cannot_overrun_a_limit(limits, send):
    # The daily limit, because a slow database can outlast the minute window.
    limits.AI_REQUESTS_PER_DAY = 2
    workers = 4
    start = threading.Barrier(workers)

    def call_once() -> bool:
        try:
            start.wait()
            generate(CHAT, "hi")
            return True
        except Throttled:
            return False
        finally:
            connection.close()

    with ThreadPoolExecutor(workers) as pool:
        results = [future.result() for future in [pool.submit(call_once) for _ in range(workers)]]

    assert sum(results) == 2
    assert AICall.objects.count() == 2


# embed: the same limits and log, on the embedding model's own quota


@pytest.mark.django_db
def test_embed_returns_vectors_and_logs_the_call_without_its_text(limits, embedder, team, member):
    vectors = embed(["secret plan"], dimensions=2, user=member, team=team)

    assert vectors == [[0.5, 0.5]]
    call = AICall.objects.get()
    assert call.feature == EMBED
    assert call.model == limits.AI_EMBEDDING_MODEL
    assert call.status == AICall.Status.SUCCEEDED
    assert (call.user, call.team) == (member, team)
    assert "secret plan" not in str(model_to_dict(call))


@pytest.mark.django_db
def test_embed_passes_its_options_to_the_provider(limits, monkeypatch):
    received = {}

    def fake_embed(texts, **options):
        received.update(options)
        return [[1.0]]

    monkeypatch.setattr(provider, "embed", fake_embed)

    embed(["hi"], dimensions=1, timeout=4.0)

    assert received == {"dimensions": 1, "timeout": 4.0}


@pytest.mark.django_db
def test_chat_and_embedding_count_separately(limits, send, embedder):
    # Both at 1, so a call counted against the other model's quota would be refused.
    limits.AI_REQUESTS_PER_MINUTE = 1
    limits.AI_EMBEDDING_REQUESTS_PER_MINUTE = 1

    generate(CHAT, "hi")
    embed(["hi"], dimensions=2)

    assert len(send) == 1
    assert len(embedder) == 1


@pytest.mark.django_db
def test_embedding_does_not_use_up_the_chat_day(limits, send, embedder):
    limits.AI_REQUESTS_PER_DAY = 1
    limits.AI_EMBEDDING_REQUESTS_PER_DAY = 1

    embed(["hi"], dimensions=2)
    generate(CHAT, "hi")

    assert len(send) == 1


@pytest.mark.django_db
def test_embed_minute_limit_stops_the_call_before_it_is_sent(limits, embedder):
    limits.AI_EMBEDDING_REQUESTS_PER_MINUTE = 1
    embed(["hi"], dimensions=2)

    with pytest.raises(Throttled) as refusal:
        embed(["hi"], dimensions=2)

    assert refusal.value.wait == 60
    assert len(embedder) == 1


@pytest.mark.django_db
def test_embed_day_limit_stops_the_call_until_midnight_pacific(limits, embedder, clock):
    clock(NOON)
    limits.AI_EMBEDDING_REQUESTS_PER_DAY = 1
    embed(["hi"], dimensions=2)

    with pytest.raises(Throttled) as refusal:
        embed(["hi"], dimensions=2)

    assert refusal.value.wait == 12 * 3600
    assert len(embedder) == 1


@pytest.mark.django_db
def test_embed_is_not_held_to_the_chat_limit_for_one_person(limits, embedder, member):
    limits.AI_REQUESTS_PER_USER_PER_DAY = 0

    embed(["hi"], dimensions=2, user=member)

    assert len(embedder) == 1


@pytest.mark.django_db
def test_an_embed_failure_is_logged_and_hides_its_details(limits, monkeypatch):
    def fail(texts, **options):
        raise provider.ProviderError("key=abc rejected")

    monkeypatch.setattr(provider, "embed", fail)

    with pytest.raises(AIUnavailable) as refusal:
        embed(["hi"], dimensions=2)

    assert "abc" not in str(refusal.value.detail)
    call = AICall.objects.get()
    assert call.status == AICall.Status.FAILED
    assert "rejected" in call.error


@pytest.mark.django_db
def test_the_providers_quota_refusal_on_embed_reads_as_throttling(limits, monkeypatch):
    def refuse(texts, **options):
        raise provider.QuotaExceeded("429")

    monkeypatch.setattr(provider, "embed", refuse)

    with pytest.raises(Throttled):
        embed(["hi"], dimensions=2)

    assert AICall.objects.get().status == AICall.Status.FAILED


# provider: the real SDK, with only the HTTP transport faked


def interaction(status="completed", **fields) -> dict:
    return {"id": "abc", "status": status, "model": "gemini-test", **fields}


@pytest.fixture
def gemini(monkeypatch):
    provider._client.cache_clear()
    wire = SimpleNamespace(requests=[], answer=(200, interaction()))

    def handle_request(transport, request):
        wire.requests.append(request)
        assert len(wire.requests) < 5, "The SDK is looping, so fail instead of hanging."
        if isinstance(wire.answer, Exception):
            raise wire.answer
        status, body = wire.answer
        return httpx.Response(status, json=body, request=request)

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", handle_request)
    yield wire
    provider._client.cache_clear()


def test_send_keeps_data_off_googles_storage_and_the_key_out_of_the_url(gemini, settings):
    provider.send("hi", system="Be brief", tools=[{"type": "function", "name": "lookup"}])

    request = gemini.requests[0]
    body = json.loads(request.content)
    assert body["store"] is False
    assert body["model"] == settings.AI_MODEL
    assert body["input"] == "hi"
    assert body["system_instruction"] == "Be brief"
    assert body["tools"][0]["name"] == "lookup"
    assert request.headers["x-goog-api-key"] == "test-only"
    assert "test-only" not in str(request.url)


def test_send_cannot_hold_a_worker_past_its_timeout(gemini):
    provider.send("hi")

    assert gemini.requests[0].extensions["timeout"]["read"] == provider.TIMEOUT_MS / 1000


def test_send_can_cut_a_request_short(gemini):
    provider.send("hi", timeout=5.5)

    assert gemini.requests[0].extensions["timeout"]["read"] == 5.5


def test_send_can_forbid_tool_calls(gemini):
    provider.send("hi", tool_choice="none")

    assert json.loads(gemini.requests[0].content)["generation_config"]["tool_choice"] == "none"


def test_send_omits_options_nobody_set(gemini):
    provider.send("hi")

    body = json.loads(gemini.requests[0].content)
    assert "system_instruction" not in body
    assert "tools" not in body
    assert "generation_config" not in body


@pytest.mark.parametrize(
    ("answer", "error"),
    [
        ((429, {"error": {"message": "quota"}}), provider.QuotaExceeded),
        ((503, {"error": {"message": "busy"}}), provider.ProviderError),
        ((500, {"error": {"message": "broken"}}), provider.ProviderError),
        ((400, {"error": {"message": "bad"}}), provider.ProviderError),
        (httpx.ReadTimeout("slow"), provider.ProviderError),
        (httpx.ConnectError("down"), provider.ProviderError),
    ],
)
def test_send_never_retries_a_failure(gemini, answer, error):
    gemini.answer = answer

    with pytest.raises(error):
        provider.send("hi")

    assert len(gemini.requests) == 1


def embeddings(*vectors) -> tuple[int, dict]:
    return 200, {"embeddings": [{"values": vector} for vector in vectors]}


def test_embed_sends_one_request_and_gets_one_vector_per_text(gemini, settings):
    gemini.answer = embeddings([0.1, 0.2], [0.3, 0.4])

    vectors = provider.embed(["first", "second"], dimensions=2)

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]
    assert len(gemini.requests) == 1
    request = gemini.requests[0]
    assert f"{settings.AI_EMBEDDING_MODEL}:batchEmbedContents" in str(request.url)
    assert request.headers["x-goog-api-key"] == "test-only"
    assert "test-only" not in str(request.url)
    entries = json.loads(request.content)["requests"]
    assert [entry["content"]["parts"][0]["text"] for entry in entries] == ["first", "second"]
    assert all(entry["outputDimensionality"] == 2 for entry in entries)


def test_embed_cannot_hold_a_worker_past_its_timeout(gemini):
    gemini.answer = embeddings([0.1])

    provider.embed(["hi"], dimensions=1)

    assert gemini.requests[0].extensions["timeout"]["read"] == provider.TIMEOUT_MS / 1000


def test_embed_can_cut_a_request_short(gemini):
    gemini.answer = embeddings([0.1])

    provider.embed(["hi"], dimensions=1, timeout=5.5)

    assert gemini.requests[0].extensions["timeout"]["read"] == 5.5


@pytest.mark.parametrize(
    ("answer", "error"),
    [
        ((429, {"error": {"message": "quota"}}), provider.QuotaExceeded),
        ((503, {"error": {"message": "busy"}}), provider.ProviderError),
        ((500, {"error": {"message": "broken"}}), provider.ProviderError),
        ((400, {"error": {"message": "bad"}}), provider.ProviderError),
        (httpx.ReadTimeout("slow"), provider.ProviderError),
        (httpx.ConnectError("down"), provider.ProviderError),
    ],
)
def test_embed_never_retries_a_failure(gemini, answer, error):
    gemini.answer = answer

    with pytest.raises(error):
        provider.embed(["hi"], dimensions=1)

    assert len(gemini.requests) == 1


@pytest.mark.parametrize("answer", [embeddings([0.1]), (200, {})])
def test_embed_refuses_a_reply_that_cannot_be_matched_to_its_texts(gemini, answer):
    gemini.answer = answer

    with pytest.raises(provider.ProviderError):
        provider.embed(["first", "second"], dimensions=1)


def test_send_never_follows_a_continuation(gemini):
    gemini.answer = (200, interaction("requires_continuation", continuation_token="next"))

    assert provider.send("hi").status == "requires_continuation"
    assert len(gemini.requests) == 1


def test_send_reads_text_and_usage(gemini):
    gemini.answer = (
        200,
        interaction(
            steps=[{"type": "model_output", "content": [{"type": "text", "text": "Hello"}]}],
            usage={"total_input_tokens": 10, "total_output_tokens": 2, "total_tokens": 15},
        ),
    )

    reply = provider.send("hi")

    assert (reply.status, reply.text) == ("completed", "Hello")
    assert (reply.input_tokens, reply.output_tokens, reply.total_tokens) == (10, 2, 15)


def test_send_survives_a_reply_with_no_steps_or_usage(gemini):
    gemini.answer = (200, interaction("failed"))

    reply = provider.send("hi")

    assert (reply.text, reply.steps, reply.total_tokens) == ("", [], None)


def test_a_tool_round_trip_can_replay_the_history(gemini):
    """The stateless loop Phase 4 needs: the model's steps go back exactly as received."""
    call = {"type": "function_call", "id": "c1", "name": "lookup", "arguments": {"id": 1}}
    thought = {"type": "thought", "signature": "opaque"}
    gemini.answer = (200, interaction("requires_action", steps=[thought, call]))
    history = [{"type": "user_input", "content": [{"type": "text", "text": "hi"}]}]

    first = provider.send(history)
    result = {
        "type": "function_result",
        "name": "lookup",
        "call_id": first.steps[1]["id"],
        "result": [{"type": "text", "text": "{}"}],
    }
    provider.send([*history, *first.steps, result])

    sent = json.loads(gemini.requests[1].content)["input"]
    assert [step["type"] for step in sent] == [
        "user_input",
        "thought",
        "function_call",
        "function_result",
    ]
    assert sent[1]["signature"] == "opaque"
    assert sent[2]["arguments"] == {"id": 1}
    assert sent[3]["call_id"] == "c1"


# admin


@pytest.mark.django_db
def test_generate_hands_the_callers_options_to_the_provider(limits, monkeypatch):
    seen = {}

    def fake_send(prompt, **options):
        seen.update(options)
        return REPLY

    monkeypatch.setattr(provider, "send", fake_send)

    generate(CHAT, "hi", system="Be brief", tools=[{}], tool_choice="none", timeout=5.5)

    assert seen == {"system": "Be brief", "tools": [{}], "tool_choice": "none", "timeout": 5.5}


@pytest.mark.django_db
def test_admin_can_read_the_log_but_not_change_it(admin_client):
    call = AICallFactory()
    pages = [
        ("changelist", [], 200),
        ("change", [call.pk], 200),
        ("add", [], 403),
        ("delete", [call.pk], 403),
    ]

    for page, args, status in pages:
        url = reverse(f"admin:ai_aicall_{page}", args=args)
        assert admin_client.get(url).status_code == status, url


@pytest.mark.django_db
def test_deleting_a_user_keeps_their_calls_on_the_log():
    user = UserFactory()
    call = AICallFactory(user=user)

    user.delete()

    call.refresh_from_db()
    assert call.user is None
