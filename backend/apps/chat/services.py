from django.contrib.auth import get_user_model
from django.db.models import QuerySet

from apps.chat.models import Message
from apps.teams.services import get_membership

User = get_user_model()


def team_messages(user: User, team_id: int) -> QuerySet[Message]:
    get_membership(user, team_id)
    return Message.objects.filter(team_id=team_id).select_related("author")


def post_message(actor: User, team_id: int, *, body: str) -> Message:
    get_membership(actor, team_id)
    return Message.objects.create(team_id=team_id, author=actor, body=body)
