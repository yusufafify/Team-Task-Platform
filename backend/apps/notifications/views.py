from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.notifications import services
from apps.notifications.models import Notification
from apps.notifications.serializers import (
    DeviceTokenSerializer,
    NotificationFilterSerializer,
    NotificationSerializer,
)


@extend_schema_view(list=extend_schema(parameters=[NotificationFilterSerializer]))
class NotificationViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Notification.objects.none()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        filters = NotificationFilterSerializer(data=self.request.query_params)
        filters.is_valid(raise_exception=True)
        return services.notifications_for(self.request.user, **filters.validated_data)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def read(self, request, pk):
        notification = services.mark_read(request.user, pk)
        return Response(self.get_serializer(notification).data)

    @extend_schema(request=None, responses={204: None})
    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        services.mark_all_read(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DeviceTokenCreateView(generics.CreateAPIView):
    serializer_class = DeviceTokenSerializer

    def perform_create(self, serializer):
        serializer.instance = services.register_device(
            self.request.user, serializer.validated_data["token"]
        )


class DeviceTokenDetailView(APIView):
    @extend_schema(responses={204: None})
    def delete(self, request, token):
        serializer = DeviceTokenSerializer(data={"token": token})
        serializer.is_valid(raise_exception=True)
        services.unregister_device(request.user, serializer.validated_data["token"])
        return Response(status=status.HTTP_204_NO_CONTENT)
