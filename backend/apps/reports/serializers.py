from rest_framework import serializers

from apps.reports.models import MonthlyReport
from apps.tasks.serializers import StatsSerializer


class ReportMemberSerializer(serializers.Serializer):
    name = serializers.CharField()
    stats = StatsSerializer()


class MonthlyReportSerializer(serializers.ModelSerializer):
    stats = StatsSerializer()
    members = ReportMemberSerializer(many=True)

    class Meta:
        model = MonthlyReport
        fields = ["id", "month", "stats", "members", "body", "created_at"]
