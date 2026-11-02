from django.urls import path

from apps.assistant import views

urlpatterns = [
    path("teams/<int:team_id>/assistant/messages/", views.AssistantMessageListView.as_view()),
]
