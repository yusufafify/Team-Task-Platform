import pytest

from apps.chat.models import Message
from tests.factories import MessageFactory

pytestmark = pytest.mark.django_db


def messages_url(team):
    return f"/api/v1/teams/{team.pk}/messages/"


def test_a_member_posts_as_themselves(api, team, member):
    response = api(member).post(messages_url(team), {"body": "Hello", "author": 999})

    assert response.status_code == 201
    assert response.json()["author"]["id"] == member.pk
    assert Message.objects.get().team == team


def test_messages_list_newest_first_and_cursor_pages_do_not_overlap(api, team, member):
    messages = [MessageFactory(team=team, author=member) for _ in range(25)]
    client = api(member)

    first = client.get(messages_url(team)).json()
    MessageFactory(team=team, author=member)
    second = client.get(first["next"]).json()

    ids = [row["id"] for row in first["results"] + second["results"]]
    assert ids == [message.pk for message in reversed(messages)]


def test_chat_is_invisible_to_outsiders(api, team, member, outsider):
    MessageFactory(team=team, author=member)
    client = api(outsider)

    assert client.get(messages_url(team)).status_code == 404
    assert client.post(messages_url(team), {"body": "Hi"}).status_code == 404
    assert Message.objects.count() == 1


@pytest.mark.parametrize("body", ["", "   ", "x" * 5001])
def test_a_message_needs_a_reasonable_body(api, team, member, body):
    assert api(member).post(messages_url(team), {"body": body}).status_code == 400
