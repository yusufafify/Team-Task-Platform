from django.urls import path
from rest_framework.routers import SimpleRouter

from apps.teams import views

router = SimpleRouter()
router.register("teams", views.TeamViewSet)

urlpatterns = [
    *router.urls,
    path("teams/<int:team_id>/members/", views.MemberListView.as_view()),
    path("teams/<int:team_id>/members/<int:user_id>/", views.MemberDetailView.as_view()),
]
