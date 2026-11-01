from django.urls import path

from apps.chat import views

urlpatterns = [
    path("teams/<int:team_id>/messages/", views.MessageListView.as_view()),
]
