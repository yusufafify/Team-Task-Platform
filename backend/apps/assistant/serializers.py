from rest_framework import serializers

from apps.assistant.models import AssistantMessage


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = ["id", "role", "body", "created_at"]


class QuestionSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=2000)


class TurnSerializer(serializers.Serializer):
    question = AssistantMessageSerializer()
    answer = AssistantMessageSerializer()
    cached = serializers.BooleanField(help_text="True when no AI request was spent.")
