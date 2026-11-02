from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "team", "author", "body", "created_at"]
        read_only_fields = ["team"]
        extra_kwargs = {"body": {"max_length": 5000}}
