from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet

from apps.chat.models import Message
from apps.chat.serializers import MessageSerializer
from apps.notifications.services import push
from apps.teams.models import TeamMembership
from apps.teams.services import get_membership

User = get_user_model()


def team_messages(user: User, team_id: int) -> QuerySet[Message]:
    get_membership(user, team_id)
    return Message.objects.filter(team_id=team_id).select_related("author")


def post_message(actor: User, team_id: int, *, body: str) -> Message:
    get_membership(actor, team_id)
    message = Message.objects.create(team_id=team_id, author=actor, body=body)
    data = MessageSerializer(message).data
    # Read at send time, so someone removed from the team hears nothing, even on an open socket.
    members = TeamMembership.objects.filter(team_id=team_id).values_list("user_id", flat=True)
    # robust: a failed push must not turn an already saved message into an error.
    transaction.on_commit(lambda: push(members, "message", data), robust=True)
    return message
