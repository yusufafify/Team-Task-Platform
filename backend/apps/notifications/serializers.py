from rest_framework import serializers

from apps.notifications.models import DeviceToken, Notification, expo_token_validator


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "kind", "title", "body", "task", "read_at", "created_at"]
        read_only_fields = fields


class NotificationFilterSerializer(serializers.Serializer):
    unread = serializers.BooleanField(required=False)


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["token", "created_at"]
        # No uniqueness check: registering a known token moves it to the requester.
        extra_kwargs = {"token": {"validators": [expo_token_validator]}}
