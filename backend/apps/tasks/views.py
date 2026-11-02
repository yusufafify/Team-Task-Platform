from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.tasks import services
from apps.tasks.models import Comment, Task
from apps.tasks.serializers import (
    CommentSerializer,
    StatsQuerySerializer,
    TaskCreateSerializer,
    TaskFilterSerializer,
    TaskSerializer,
    TeamStatsSerializer,
)


@extend_schema_view(list=extend_schema(parameters=[TaskFilterSerializer]))
class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.none()
    serializer_class = TaskSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_serializer_class(self):
        return TaskCreateSerializer if self.action == "create" else TaskSerializer

    def get_queryset(self):
        tasks = services.visible_tasks(self.request.user).order_by("due_at", "id")
        if self.action != "list":
            return tasks
        filters = TaskFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        return services.filter_tasks(tasks, **filters.validated_data)

    def perform_create(self, serializer):
        serializer.instance = services.create_task(self.request.user, **serializer.validated_data)

    def perform_update(self, serializer):
        services.update_task(self.request.user, serializer.instance, **serializer.validated_data)

    def perform_destroy(self, instance):
        services.delete_task(self.request.user, instance)


class CommentListView(generics.ListCreateAPIView):
    queryset = Comment.objects.none()
    serializer_class = CommentSerializer

    def get_queryset(self):
        return services.list_comments(self.request.user, self.kwargs["task_id"])

    def perform_create(self, serializer):
        serializer.instance = services.add_comment(
            self.request.user, self.kwargs["task_id"], **serializer.validated_data
        )


class TeamStatsView(APIView):
    @extend_schema(parameters=[StatsQuerySerializer], responses=TeamStatsSerializer)
    def get(self, request, team_id):
        query = StatsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        stats = services.team_stats(request.user, team_id, **query.validated_data)
        return Response(TeamStatsSerializer(stats).data)
