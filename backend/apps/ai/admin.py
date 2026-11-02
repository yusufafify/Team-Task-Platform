from django.contrib import admin

from .models import AICall


@admin.register(AICall)
class AICallAdmin(admin.ModelAdmin):
    """Read-only: these rows are the rate limits' counter, so an edit would change the limits."""

    list_display = ("created_at", "feature", "status", "user", "team", "total_tokens", "latency_ms")
    list_filter = ("feature", "status")
    list_select_related = ("user", "team")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
