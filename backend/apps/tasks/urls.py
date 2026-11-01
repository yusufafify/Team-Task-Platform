from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.tasks import views

router = SimpleRouter()
router.register("tasks", views.TaskViewSet)

urlpatterns = [
    *router.urls,
    path("tasks/<int:task_id>/comments/", views.CommentListView.as_view()),
    path("teams/<int:team_id>/stats/", views.TeamStatsView.as_view()),
]
