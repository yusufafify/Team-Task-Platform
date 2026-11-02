from django.contrib import admin

from .models import Team, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    autocomplete_fields = ("user",)
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "timezone", "created_at")
    search_fields = ("name",)
    inlines = (TeamMembershipInline,)
