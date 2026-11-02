import factory
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.ai.models import AICall
from apps.chat.models import Message
from apps.notifications.models import Notification
from apps.tasks.models import Comment, Task
from apps.teams.models import Team, TeamMembership


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")


class MembershipFactory(DjangoModelFactory):
    class Meta:
        model = TeamMembership

    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    team = factory.SubFactory(TeamFactory)
    title = "Prepare the report"
    created_by = factory.SubFactory(UserFactory)
    due_at = factory.LazyFunction(timezone.now)


class CommentFactory(DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    body = "Looks good"


class MessageFactory(DjangoModelFactory):
    class Meta:
        model = Message

    team = factory.SubFactory(TeamFactory)
    author = factory.SubFactory(UserFactory)
    body = "Hello team"


class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    recipient = factory.SubFactory(UserFactory)
    kind = Notification.Kind.TASK_ASSIGNED
    title = "You were assigned"


class AICallFactory(DjangoModelFactory):
    class Meta:
        model = AICall

    feature = AICall.Feature.CHAT
    # The configured model, because the limits count one model's calls.
    model = factory.LazyFunction(lambda: settings.AI_MODEL)
