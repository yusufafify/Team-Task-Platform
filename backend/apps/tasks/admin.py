from django.contrib import admin

from .models import Comment, Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "team", "status", "priority", "assignee", "due_at")
    list_filter = ("status", "priority", "team")
    list_select_related = ("team", "assignee")
    search_fields = ("title",)
    autocomplete_fields = ("team", "assignee", "created_by")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("task", "author", "created_at")
    list_select_related = ("task", "author")
    autocomplete_fields = ("task", "author")
