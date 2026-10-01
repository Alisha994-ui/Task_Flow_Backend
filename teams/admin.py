from django.contrib import admin
from .models import Team, TeamMember


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "team_lead",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
        "team_lead__username",
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):

    list_display = (
        "team",
        "user",
        "joined_at",
    )

    list_filter = (
        "team",
    )

    search_fields = (
        "team__name",
        "user__username",
        "user__email",
    )