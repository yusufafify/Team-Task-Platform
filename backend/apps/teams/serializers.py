from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.teams.models import Team, TeamMembership


class TeamSerializer(serializers.ModelSerializer):
    role = serializers.ChoiceField(
        choices=TeamMembership.Role.choices,
        read_only=True,
        help_text="The requester's role on this team.",
    )

    class Meta:
        model = Team
        fields = ["id", "name", "timezone", "role", "created_at"]


class MemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TeamMembership
        fields = ["user", "role", "joined_at"]
        read_only_fields = fields


class MemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=TeamMembership.Role.choices)


class AddMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=TeamMembership.Role.choices, default=TeamMembership.Role.MEMBER
    )
