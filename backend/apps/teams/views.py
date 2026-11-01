from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.response import Response

from apps.teams import services
from apps.teams.models import Team, TeamMembership
from apps.teams.serializers import (
    AddMemberSerializer,
    MemberRoleSerializer,
    MemberSerializer,
    TeamSerializer,
)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.none()
    serializer_class = TeamSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return services.teams_for(self.request.user)

    def perform_create(self, serializer):
        team = services.create_team(self.request.user, **serializer.validated_data)
        serializer.instance = self.get_queryset().get(pk=team.pk)

    def perform_update(self, serializer):
        services.update_team(self.request.user, serializer.instance, **serializer.validated_data)

    def perform_destroy(self, instance):
        services.delete_team(self.request.user, instance)


class MemberListView(generics.ListAPIView):
    queryset = TeamMembership.objects.none()
    serializer_class = MemberSerializer
    # A roster is small, and clients need all of it for assignee pickers.
    pagination_class = None

    def get_queryset(self):
        return services.list_members(self.request.user, self.kwargs["team_id"])

    @extend_schema(request=AddMemberSerializer, responses={201: MemberSerializer})
    def post(self, request, team_id):
        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = services.add_member(request.user, team_id, **serializer.validated_data)
        return Response(MemberSerializer(membership).data, status=status.HTTP_201_CREATED)


class MemberDetailView(generics.GenericAPIView):
    queryset = TeamMembership.objects.none()
    serializer_class = MemberSerializer

    @extend_schema(request=MemberRoleSerializer)
    def patch(self, request, team_id, user_id):
        serializer = MemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = services.change_member_role(
            request.user, team_id, user_id, **serializer.validated_data
        )
        return Response(self.get_serializer(membership).data)

    @extend_schema(responses={204: None})
    def delete(self, request, team_id, user_id):
        services.remove_member(request.user, team_id, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
