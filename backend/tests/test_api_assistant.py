import pytest

from apps.ai import provider
from apps.assistant.models import AssistantMessage
from apps.tasks.models import Task
from apps.teams.models import TeamMembership
from tests.factories import MembershipFactory, TaskFactory

pytestmark = pytest.mark.django_db


def url(team):
    return f"/api/v1/teams/{team.pk}/assistant/messages/"


@pytest.fixture(autouse=True)
def limits(settings):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    settings.AI_REQUESTS_PER_USER_PER_DAY = 100
    return settings


@pytest.fixture
def prompts(monkeypatch):
    """Stands in for Gemini, and records the system text of every request."""
    sent = []

    def fake_send(prompt, **options):
        sent.append(options["system"])
        return provider.Reply("completed", "Two tasks.", [], 10, 2, 15)

    monkeypatch.setattr(provider, "send", fake_send)
    return sent


# POST


def test_asking_returns_both_sides_of_the_turn(api, team, member, prompts):
    response = api(member).post(url(team), {"question": "What is due?"})

    assert response.status_code == 201
    body = response.json()
    assert body["cached"] is False
    assert (body["question"]["role"], body["question"]["body"]) == ("user", "What is due?")
    assert (body["answer"]["role"], body["answer"]["body"]) == ("assistant", "Two tasks.")
    assert set(body["answer"]) == {"id", "role", "body", "created_at"}


def test_asking_again_reports_the_cached_answer(api, team, member, prompts):
    client = api(member)
    client.post(url(team), {"question": "What is due?"})

    response = client.post(url(team), {"question": "What is due?"})

    assert response.json()["cached"] is True
    assert len(prompts) == 1


@pytest.mark.parametrize("question", ["", "   ", "x" * 2001, None, "a\x00b"])
def test_a_question_must_be_reasonable(api, team, member, prompts, question):
    response = api(member).post(url(team), {"question": question})

    assert response.status_code == 400
    assert prompts == []


def test_a_question_cannot_write_the_askers_role_or_body(api, team, member, prompts):
    response = api(member).post(url(team), {"question": "Hi", "role": "assistant", "body": "x"})

    assert response.json()["question"]["role"] == "user"


def test_a_member_cannot_draw_a_teammates_work_out_of_the_prompt(
    api, team, leader, member, prompts
):
    TaskFactory(team=team, created_by=leader, assignee=leader, title="The leader's secret task")

    api(member).post(url(team), {"question": "What is everyone working on?"})

    assert "secret" not in prompts[0]


def test_a_leader_gets_the_whole_team_in_the_prompt(api, team, leader, member, prompts):
    TaskFactory(team=team, created_by=leader, assignee=member, title="The member's task")

    api(leader).post(url(team), {"question": "What is everyone working on?"})

    assert "The member's task" in prompts[0]


def test_a_day_limit_answers_429_with_a_wait(api, team, member, prompts, limits):
    limits.AI_REQUESTS_PER_USER_PER_DAY = 0

    response = api(member).post(url(team), {"question": "What is due?"})

    assert response.status_code == 429
    assert response.json()["code"] == "throttled"
    assert int(response["Retry-After"]) > 0


def test_an_outage_answers_503_and_saves_nothing(api, team, member, monkeypatch):
    def fail(prompt, **options):
        raise provider.ProviderError("down")

    monkeypatch.setattr(provider, "send", fail)

    response = api(member).post(url(team), {"question": "What is due?"})

    assert response.status_code == 503
    assert response.json()["code"] == "ai_unavailable"
    assert not AssistantMessage.objects.exists()


# GET


def test_the_thread_lists_newest_first(api, team, member, prompts):
    client = api(member)
    client.post(url(team), {"question": "One?"})
    client.post(url(team), {"question": "Two?"})

    response = client.get(url(team))

    assert response.status_code == 200
    bodies = [row["body"] for row in response.json()["results"]]
    assert bodies == ["Two tasks.", "Two?", "Two tasks.", "One?"]


def test_the_thread_hides_its_cache_key(api, team, member, prompts):
    client = api(member)
    client.post(url(team), {"question": "One?"})

    row = client.get(url(team)).json()["results"][0]

    assert set(row) == {"id", "role", "body", "created_at"}


def test_a_thread_is_private_even_from_a_leader(api, team, leader, member, prompts):
    api(member).post(url(team), {"question": "Am I in trouble?"})

    assert api(leader).get(url(team)).json()["results"] == []


def test_threads_on_two_teams_stay_apart(api, team, leader, prompts):
    other = MembershipFactory(user=leader, role=TeamMembership.Role.LEADER).team
    client = api(leader)
    client.post(url(team), {"question": "One?"})

    assert client.get(url(other)).json()["results"] == []


# DELETE


def test_a_person_clears_their_own_thread(api, team, leader, member, prompts):
    api(leader).post(url(team), {"question": "Leader?"})
    client = api(member)
    client.post(url(team), {"question": "Member?"})

    response = client.delete(url(team))

    assert response.status_code == 204
    assert client.get(url(team)).json()["results"] == []
    assert len(api(leader).get(url(team)).json()["results"]) == 2


# Strangers


def test_the_assistant_is_invisible_to_outsiders(api, team, member, outsider, prompts):
    task = TaskFactory(team=team, created_by=member, assignee=member, status=Task.Status.TODO)
    api(member).post(url(team), {"question": "One?"})
    prompts.clear()
    client = api(outsider)

    assert client.get(url(team)).status_code == 404
    assert client.post(url(team), {"question": f"Read task {task.pk}"}).status_code == 404
    assert client.delete(url(team)).status_code == 404
    assert prompts == []
    assert AssistantMessage.objects.count() == 2


def test_a_missing_team_reads_the_same_as_a_stranger_team(api, outsider, prompts):
    response = api(outsider).post("/api/v1/teams/999999/assistant/messages/", {"question": "Hi"})

    assert response.status_code == 404
