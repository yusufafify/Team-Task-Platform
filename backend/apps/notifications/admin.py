from django.contrib import admin

from .models import DeviceToken, Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "recipient", "read_at", "created_at")
    list_filter = ("kind",)
    list_select_related = ("recipient",)
    autocomplete_fields = ("recipient", "task")


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at")
    list_select_related = ("user",)
    autocomplete_fields = ("user",)
