from rest_framework import generics

from apps.reports import services
from apps.reports.models import MonthlyReport
from apps.reports.serializers import MonthlyReportSerializer


class MonthlyReportListView(generics.ListAPIView):
    queryset = MonthlyReport.objects.none()
    serializer_class = MonthlyReportSerializer

    def get_queryset(self):
        return services.reports_for(self.request.user, self.kwargs["team_id"])
