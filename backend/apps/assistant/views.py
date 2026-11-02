from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from apps.assistant import services
from apps.assistant.models import AssistantMessage
from apps.assistant.serializers import (
    AssistantMessageSerializer,
    QuestionSerializer,
    TurnSerializer,
)
from apps.chat.views import MessagePagination


class AssistantMessageListView(generics.ListAPIView):
    queryset = AssistantMessage.objects.none()
    serializer_class = AssistantMessageSerializer
    pagination_class = MessagePagination

    def get_queryset(self):
        return services.thread(self.request.user, self.kwargs["team_id"])

    @extend_schema(request=QuestionSerializer, responses={201: TurnSerializer})
    def post(self, request, team_id):
        question = QuestionSerializer(data=request.data)
        question.is_valid(raise_exception=True)
        turn = services.ask(request.user, team_id, question.validated_data["question"])
        return Response(TurnSerializer(turn).data, status=status.HTTP_201_CREATED)

    @extend_schema(responses={204: None})
    def delete(self, request, team_id):
        services.clear(request.user, team_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
