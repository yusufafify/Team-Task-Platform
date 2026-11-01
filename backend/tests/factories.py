import factory
from django.contrib.auth import get_user_model
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.tasks.models import Task
from apps.teams.models import Team


class UserFactory(DjangoModelFactory):
    class Meta:
        model = get_user_model()

    email = factory.Sequence(lambda n: f"user{n}@example.com")


class TeamFactory(DjangoModelFactory):
    class Meta:
        model = Team

    name = factory.Sequence(lambda n: f"Team {n}")


class TaskFactory(DjangoModelFactory):
    class Meta:
        model = Task

    team = factory.SubFactory(TeamFactory)
    title = "Prepare the report"
    created_by = factory.SubFactory(UserFactory)
    due_at = factory.LazyFunction(timezone.now)
