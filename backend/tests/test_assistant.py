import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from rest_framework.exceptions import NotFound, Throttled

from apps.ai import provider
from apps.ai.models import AICall
from apps.ai.services import AIUnavailable
from apps.assistant import services
from apps.assistant.models import AssistantMessage
from apps.tasks.models import Task
from apps.tasks.services import update_task
from apps.teams.models import TeamMembership
from apps.teams.services import change_member_role, remove_member
from tests.factories import MembershipFactory, TaskFactory, UserFactory

pytestmark = pytest.mark.django_db

USER = AssistantMessage.Role.USER
ASSISTANT = AssistantMessage.Role.ASSISTANT


def answer(text="Two tasks are overdue."):
    step = {"type": "model_output", "content": [{"type": "text", "text": text}]}
    return provider.Reply("completed", text, [step], 10, 2, 15)


def wants(*calls):
    """A reply asking for tools, with a thought step, as a real one has."""
    steps = [{"type": "thought", "signature": "opaque"}]
    for number, (name, arguments) in enumerate(calls):
        call = {"type": "function_call", "id": f"c{number}", "name": name, "arguments": arguments}
        steps.append(call)
    return provider.Reply("requires_action", "", steps, 10, 2, 15)


class FakeModel:
    """Stands in for Gemini, plays back `replies`, and records every request."""

    def __init__(self):
        self.replies = []
        self.requests = []
        self.delay = 0

    def __call__(self, prompt, **options):
        self.requests.append({"prompt": prompt, **options})
        time.sleep(self.delay)
        reply = self.replies.pop(0) if self.replies else answer()
        if isinstance(reply, Exception):
            raise reply
        return reply


@pytest.fixture(autouse=True)
def limits(settings):
    settings.AI_REQUESTS_PER_MINUTE = 100
    settings.AI_REQUESTS_PER_DAY = 100
    settings.AI_REQUESTS_PER_USER_PER_DAY = 100
    return settings


@pytest.fixture
def model(monkeypatch):
    fake = FakeModel()
    monkeypatch.setattr(provider, "send", fake)
    return fake


@pytest.fixture
def clock(monkeypatch):
    def set_time(moment: datetime) -> None:
        monkeypatch.setattr(timezone, "now", lambda: moment)

    return set_time


def snapshot_of(user, team):
    return services.build_snapshot(user, TeamMembership.objects.get(user=user, team=team))


def titles(snapshot):
    return [task["title"] for task in snapshot["open_tasks"]["tasks"]]


def texts(steps):
    return [(step["type"], step["content"][0]["text"]) for step in steps]


def thread_of(user, team):
    return TeamMembership.objects.get(user=user, team=team).assistant_messages


# build_snapshot


def test_a_leader_sees_the_whole_team(team, leader, member):
    TaskFactory(team=team, created_by=leader, assignee=member, title="Theirs")
    TaskFactory(team=team, created_by=leader, assignee=leader, title="Mine")

    snapshot = snapshot_of(leader, team)

    assert sorted(titles(snapshot)) == ["Mine", "Theirs"]
    assert snapshot["stats"]["scope"] == "team"
    assert len(snapshot["stats"]["members"]) == 2


def test_a_member_sees_only_their_own_work(team, leader, member):
    TaskFactory(team=team, created_by=leader, assignee=member, title="Mine")
    TaskFactory(team=team, created_by=leader, assignee=leader, title="Theirs")
    TaskFactory(team=team, created_by=leader, title="Nobody's")

    snapshot = snapshot_of(member, team)

    assert titles(snapshot) == ["Mine"]
    assert (snapshot["stats"]["scope"], snapshot["stats"]["members"]) == ("self", [])
    assert snapshot["asker"]["role"] == "member"


def test_a_snapshot_stays_on_one_team(team, leader):
    other = MembershipFactory(user=leader, role=TeamMembership.Role.LEADER).team
    TaskFactory(team=other, created_by=leader, title="Elsewhere")

    assert titles(snapshot_of(leader, team)) == []


def test_a_snapshot_holds_no_email(team, leader, member):
    member.first_name = "Sara"
    member.save()
    TaskFactory(team=team, created_by=leader, assignee=member)

    rendered = services.render_snapshot(snapshot_of(leader, team))

    assert "Sara" in rendered
    assert "@" not in rendered


def test_open_tasks_come_soonest_first_and_done_ones_stay_apart(team, leader):
    now = timezone.now()
    TaskFactory(team=team, created_by=leader, title="Later", due_at=now + timedelta(days=2))
    TaskFactory(team=team, created_by=leader, title="Sooner", due_at=now + timedelta(days=1))
    TaskFactory(
        team=team, created_by=leader, title="Done", status=Task.Status.DONE, completed_at=now
    )

    snapshot = snapshot_of(leader, team)

    assert titles(snapshot) == ["Sooner", "Later"]
    assert [task["title"] for task in snapshot["recently_done"]] == ["Done"]


def test_a_long_list_is_cut_and_the_model_is_told(team, leader, monkeypatch):
    monkeypatch.setattr(services, "SNAPSHOT_OPEN_TASKS", 2)
    for _ in range(3):
        TaskFactory(team=team, created_by=leader)

    tasks = snapshot_of(leader, team)["open_tasks"]

    assert (tasks["total"], len(tasks["tasks"])) == (3, 2)


def test_today_is_the_teams_today(team, leader, clock):
    team.timezone = "Asia/Tokyo"
    team.save()
    clock(datetime(2026, 11, 2, 20, 0, tzinfo=UTC))

    assert snapshot_of(leader, team)["today"] == "Tuesday 2026-11-03"


def test_a_snapshot_is_the_same_until_the_data_changes(team, leader):
    TaskFactory(team=team, created_by=leader)

    first = services.render_snapshot(snapshot_of(leader, team))

    assert services.render_snapshot(snapshot_of(leader, team)) == first


def test_a_snapshots_queries_do_not_grow_with_the_team(team, leader):
    def add_people_and_work():
        user = MembershipFactory(team=team).user
        TaskFactory(team=team, created_by=leader, assignee=user)
        TaskFactory(
            team=team,
            created_by=leader,
            assignee=user,
            status=Task.Status.DONE,
            completed_at=timezone.now(),
        )

    def queries():
        with CaptureQueriesContext(connection) as captured:
            snapshot_of(leader, team)
        return len(captured)

    add_people_and_work()
    small = queries()
    for _ in range(4):
        add_people_and_work()

    assert queries() == small


# ask: one request


def test_ask_saves_the_turn_and_counts_the_request(team, member, model):
    turn = services.ask(member, team.pk, "What is overdue?")

    assert (turn.answer.body, turn.cached) == ("Two tasks are overdue.", False)
    rows = list(thread_of(member, team).order_by("id").values_list("role", "body"))
    assert rows == [(USER, "What is overdue?"), (ASSISTANT, "Two tasks are overdue.")]
    call = AICall.objects.get()
    assert (call.feature, call.user, call.team) == (AICall.Feature.CHAT, member, team)


def test_ask_sends_the_snapshot_and_the_tools(team, leader, model):
    TaskFactory(team=team, created_by=leader, title="Fix the login page")

    services.ask(leader, team.pk, "What is open?")

    request = model.requests[0]
    assert "Fix the login page" in request["system"]
    assert {tool["name"] for tool in request["tools"]} == {
        "list_tasks",
        "get_task",
        "get_stats",
        "recent_messages",
        "search",
    }
    assert request["tool_choice"] is None


def test_ask_needs_a_membership(team, outsider, model):
    with pytest.raises(NotFound):
        services.ask(outsider, team.pk, "What is open?")

    assert model.requests == []


def test_a_blank_reply_is_not_saved(team, member, model):
    model.replies = [answer("")]

    with pytest.raises(AIUnavailable):
        services.ask(member, team.pk, "What is overdue?")

    assert not thread_of(member, team).exists()


def test_a_failed_request_leaves_the_thread_as_it_was(team, member, model):
    model.replies = [provider.ProviderError("down")]

    with pytest.raises(AIUnavailable):
        services.ask(member, team.pk, "What is overdue?")

    assert not thread_of(member, team).exists()


def test_a_refused_request_reaches_no_model(team, member, model, limits):
    limits.AI_REQUESTS_PER_USER_PER_DAY = 0

    with pytest.raises(Throttled):
        services.ask(member, team.pk, "What is overdue?")

    assert model.requests == []
    assert not thread_of(member, team).exists()


# ask: history


def test_earlier_turns_go_back_to_the_model_in_order(team, member, model):
    model.replies = [answer("Two."), answer("Sara's.")]

    services.ask(member, team.pk, "How many are overdue?")
    services.ask(member, team.pk, "Whose are they?")

    assert texts(model.requests[1]["prompt"]) == [
        ("user_input", "How many are overdue?"),
        ("model_output", "Two."),
        ("user_input", "Whose are they?"),
    ]


def test_one_persons_thread_never_reaches_another(team, leader, member, model):
    services.ask(leader, team.pk, "Who is falling behind?")

    services.ask(member, team.pk, "What is due?")

    assert texts(model.requests[1]["prompt"]) == [("user_input", "What is due?")]


def test_history_keeps_only_the_newest_turns(team, member, model, monkeypatch):
    monkeypatch.setattr(services, "HISTORY_MESSAGES", 2)
    services.ask(member, team.pk, "One?")
    services.ask(member, team.pk, "Two?")

    services.ask(member, team.pk, "Three?")

    assert [text for _, text in texts(model.requests[2]["prompt"])] == [
        "Two?",
        "Two tasks are overdue.",
        "Three?",
    ]


def test_a_quiet_hour_ends_the_conversation(team, member, model, clock):
    start = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
    clock(start)
    services.ask(member, team.pk, "One?")
    clock(start + services.HISTORY_WINDOW + timedelta(minutes=1))

    services.ask(member, team.pk, "Two?")

    assert texts(model.requests[1]["prompt"]) == [("user_input", "Two?")]


# ask: tools


def test_a_tool_round_trip_replays_the_models_steps(team, leader, model):
    task = TaskFactory(team=team, created_by=leader, title="Fix the login page")
    first = wants(("get_task", {"task_id": task.pk}))
    model.replies = [first, answer("It has no comments.")]

    turn = services.ask(leader, team.pk, "Any comments on it?")

    follow_up = model.requests[1]["prompt"]
    assert [step["type"] for step in follow_up] == [
        "user_input",
        "thought",
        "function_call",
        "function_result",
    ]
    assert follow_up[1] == first.steps[0]
    assert follow_up[3]["call_id"] == "c0"
    assert "Fix the login page" in follow_up[3]["result"][0]["text"]
    assert turn.answer.body == "It has no comments."


def test_every_call_in_a_reply_gets_its_own_result(team, leader, model):
    model.replies = [wants(("get_stats", {}), ("recent_messages", {})), answer()]

    services.ask(leader, team.pk, "How are we doing?")

    results = model.requests[1]["prompt"][-2:]
    assert [step["call_id"] for step in results] == ["c0", "c1"]


def test_a_tool_refusal_goes_back_to_the_model(team, leader, model):
    model.replies = [wants(("get_task", {"task_id": "abc"})), answer("I can't find that task.")]

    turn = services.ask(leader, team.pk, "Read task abc")

    assert model.requests[1]["prompt"][-1]["is_error"] is True
    assert turn.answer.body == "I can't find that task."


def test_the_last_request_must_answer(team, leader, model):
    calls = wants(("get_stats", {}))
    model.replies = [calls] * (services.MAX_REQUESTS - 1) + [answer("Done.")]

    turn = services.ask(leader, team.pk, "Compare the last six months")

    assert [request["tool_choice"] for request in model.requests] == [None] * (
        services.MAX_REQUESTS - 1
    ) + ["none"]
    assert turn.answer.body == "Done."


def test_a_question_never_spends_more_than_its_requests(team, leader, model):
    model.replies = [wants(("get_stats", {}))] * 10

    with pytest.raises(AIUnavailable):
        services.ask(leader, team.pk, "Loop forever")

    assert len(model.requests) == services.MAX_REQUESTS
    assert not thread_of(leader, team).exists()


def test_a_limit_hit_mid_question_saves_nothing(team, leader, model):
    model.replies = [wants(("get_stats", {})), provider.QuotaExceeded("429")]

    with pytest.raises(Throttled):
        services.ask(leader, team.pk, "How are we doing?")

    assert not thread_of(leader, team).exists()


def test_requests_share_one_deadline(team, leader, model):
    model.delay = 0.05
    model.replies = [wants(("get_stats", {})), answer()]

    services.ask(leader, team.pk, "How are we doing?")

    first, second = [request["timeout"] for request in model.requests]
    assert first <= services.DEADLINE_SECONDS
    assert second <= first - model.delay


def test_a_spent_deadline_stops_the_next_request(team, leader, model, monkeypatch):
    monkeypatch.setattr(services, "DEADLINE_SECONDS", 0.0)

    with pytest.raises(AIUnavailable):
        services.ask(leader, team.pk, "How are we doing?")

    assert model.requests == []


# ask: answer cache


def test_a_repeated_question_costs_no_request(team, member, model):
    first = services.ask(member, team.pk, "What is overdue?")

    second = services.ask(member, team.pk, "What is overdue?")

    assert (second.cached, second.answer.body) == (True, first.answer.body)
    assert len(model.requests) == 1
    assert AICall.objects.count() == 1


def test_a_cached_answer_still_joins_the_thread(team, member, model):
    services.ask(member, team.pk, "What is overdue?")
    services.ask(member, team.pk, "What is overdue?")

    assert thread_of(member, team).count() == 4


def test_a_cached_answer_needs_no_quota(team, member, model, limits):
    services.ask(member, team.pk, "What is overdue?")
    limits.AI_REQUESTS_PER_USER_PER_DAY = 0

    assert services.ask(member, team.pk, "What is overdue?").cached is True


def test_case_and_spacing_do_not_matter(team, member, model):
    services.ask(member, team.pk, "What is overdue?")

    assert services.ask(member, team.pk, "  what   is OVERDUE? ").cached is True


def test_a_different_question_is_not_a_hit(team, member, model):
    services.ask(member, team.pk, "What is overdue?")

    assert services.ask(member, team.pk, "What is due?").cached is False


def test_a_change_the_asker_can_see_ends_the_cached_answer(team, leader, member, model):
    task = TaskFactory(team=team, created_by=leader, assignee=member)
    services.ask(member, team.pk, "What is overdue?")

    update_task(member, task, status=Task.Status.BLOCKED)

    assert services.ask(member, team.pk, "What is overdue?").cached is False


def test_a_change_the_asker_cannot_see_keeps_the_cached_answer(team, leader, member, model):
    services.ask(member, team.pk, "What is overdue?")

    TaskFactory(team=team, created_by=leader, assignee=leader)

    assert services.ask(member, team.pk, "What is overdue?").cached is True


def test_a_new_day_ends_the_cached_answer(team, member, model, clock):
    start = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
    clock(start)
    services.ask(member, team.pk, "What is due today?")

    clock(start + timedelta(days=1))

    assert services.ask(member, team.pk, "What is due today?").cached is False


def test_a_new_model_ends_the_cached_answer(team, member, model, limits):
    services.ask(member, team.pk, "What is overdue?")

    limits.AI_MODEL = "another-model"

    assert services.ask(member, team.pk, "What is overdue?").cached is False


def test_an_answer_is_never_shared_between_people(team, leader, model):
    other = MembershipFactory(team=team, role=TeamMembership.Role.LEADER).user
    services.ask(leader, team.pk, "What is overdue?")

    assert services.ask(other, team.pk, "What is overdue?").cached is False


def test_an_answer_that_used_a_tool_is_not_cached(team, leader, model):
    model.replies = [wants(("recent_messages", {})), answer("Sara said hello.")]
    services.ask(leader, team.pk, "What did Sara say?")

    assert services.ask(leader, team.pk, "What did Sara say?").cached is False


def test_a_follow_up_is_not_cached_because_it_leans_on_the_conversation(team, member, model):
    model.replies = [answer("Sara's."), answer("Ali's."), answer("Sara's again.")]
    services.ask(member, team.pk, "Whose is the login task?")
    services.ask(member, team.pk, "And the other one?")

    assert services.ask(member, team.pk, "And the other one?").cached is False


def test_a_standalone_question_hits_again_mid_conversation(team, member, model):
    services.ask(member, team.pk, "What is overdue?")
    services.ask(member, team.pk, "Who owns it?")

    assert services.ask(member, team.pk, "What is overdue?").cached is True


def test_the_first_question_after_a_quiet_hour_can_be_cached(team, member, model, clock):
    start = datetime(2026, 11, 2, 9, 0, tzinfo=UTC)
    clock(start)
    services.ask(member, team.pk, "One?")
    clock(start + services.HISTORY_WINDOW + timedelta(minutes=1))
    services.ask(member, team.pk, "Two?")

    assert services.ask(member, team.pk, "Two?").cached is True


# The thread


def test_clearing_the_thread_also_clears_its_cache(team, member, model):
    services.ask(member, team.pk, "What is overdue?")

    services.clear(member, team.pk)

    assert not thread_of(member, team).exists()
    assert services.ask(member, team.pk, "What is overdue?").cached is False


def test_clearing_touches_only_the_askers_thread(team, leader, member, model):
    services.ask(leader, team.pk, "Who is behind?")
    services.ask(member, team.pk, "What is due?")

    services.clear(member, team.pk)

    assert thread_of(leader, team).count() == 2


def test_a_demoted_leader_loses_answers_given_to_a_leader(team, leader, model):
    MembershipFactory(team=team, role=TeamMembership.Role.LEADER, user=(actor := UserFactory()))
    services.ask(leader, team.pk, "Who is behind?")

    change_member_role(actor, team.pk, leader.pk, role=TeamMembership.Role.MEMBER)

    assert not thread_of(leader, team).exists()


def test_a_promotion_keeps_the_thread(team, leader, member, model):
    services.ask(member, team.pk, "What is due?")

    change_member_role(leader, team.pk, member.pk, role=TeamMembership.Role.LEADER)

    assert thread_of(member, team).count() == 2


def test_leaving_a_team_removes_the_thread(team, leader, member, model):
    services.ask(member, team.pk, "What is due?")

    remove_member(leader, team.pk, member.pk)

    assert not AssistantMessage.objects.exists()


def test_a_snapshot_renders_as_json(team, leader):
    assert json.loads(services.render_snapshot(snapshot_of(leader, team)))["team"]["name"]
