from django.urls import path

from apps.reports import views

urlpatterns = [
    path("teams/<int:team_id>/reports/", views.MonthlyReportListView.as_view()),
]
