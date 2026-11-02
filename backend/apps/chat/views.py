from rest_framework import generics
from rest_framework.pagination import CursorPagination

from apps.chat import services
from apps.chat.models import Message
from apps.chat.serializers import MessageSerializer


class MessagePagination(CursorPagination):
    # A cursor, because new messages would shift page numbers between a client's requests.
    ordering = ("-created_at", "-id")


class MessageListView(generics.ListCreateAPIView):
    queryset = Message.objects.none()
    serializer_class = MessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        return services.team_messages(self.request.user, self.kwargs["team_id"])

    def perform_create(self, serializer):
        serializer.instance = services.post_message(
            self.request.user, self.kwargs["team_id"], **serializer.validated_data
        )
