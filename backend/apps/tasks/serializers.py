from django.utils import timezone
from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.tasks.models import Comment, Task


class TaskSerializer(serializers.ModelSerializer):
    # Plain integers, so the service answers for a bad team or assignee. A related field would
    # first reveal which ids exist.
    assignee = serializers.IntegerField(source="assignee_id", required=False, allow_null=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "team",
            "title",
            "description",
            "status",
            "priority",
            "assignee",
            "created_by",
            "due_at",
            "completed_at",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["team", "created_by", "completed_at"]
        extra_kwargs = {"description": {"max_length": 10000}}

    def get_is_overdue(self, task: Task) -> bool:
        return task.status != Task.Status.DONE and task.due_at < timezone.now()


class TaskCreateSerializer(TaskSerializer):
    team = serializers.IntegerField(source="team_id")


class TaskFilterSerializer(serializers.Serializer):
    team = serializers.IntegerField(required=False)
    status = serializers.ChoiceField(choices=Task.Status.choices, required=False)
    priority = serializers.ChoiceField(choices=Task.Priority.choices, required=False)
    assignee = serializers.IntegerField(required=False)
    overdue = serializers.BooleanField(required=False)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "task", "author", "body", "created_at"]
        read_only_fields = ["task"]
        extra_kwargs = {"body": {"max_length": 5000}}


class StatsQuerySerializer(serializers.Serializer):
    start = serializers.DateField(required=False, help_text="Default: first of the end's month.")
    end = serializers.DateField(required=False, help_text="Inclusive. Default: today.")


class StatsSerializer(serializers.Serializer):
    due = serializers.IntegerField()
    completed = serializers.IntegerField()
    on_time = serializers.IntegerField()
    delayed = serializers.IntegerField()
    overdue = serializers.IntegerField(help_text="Overdue right now, whatever the period.")
    completion_rate = serializers.FloatField(allow_null=True, help_text="Above 1 is possible.")
    on_time_rate = serializers.FloatField(allow_null=True)
    average_delay_days = serializers.FloatField(allow_null=True)


class MemberStatsSerializer(serializers.Serializer):
    user = UserSerializer()
    stats = StatsSerializer()


class TeamStatsSerializer(serializers.Serializer):
    start = serializers.DateField()
    end = serializers.DateField()
    timezone = serializers.CharField()
    scope = serializers.ChoiceField(choices=["team", "self"])
    stats = StatsSerializer()
    members = MemberStatsSerializer(many=True, help_text="Empty unless scope is team.")
