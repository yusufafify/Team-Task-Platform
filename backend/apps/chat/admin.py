from django.contrib import admin

from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("team", "author", "created_at")
    list_filter = ("team",)
    list_select_related = ("team", "author")
    autocomplete_fields = ("team", "author")
