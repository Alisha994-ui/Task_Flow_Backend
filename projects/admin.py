from django.contrib import admin
from .models import Project, ProjectMember,Milestone

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "manager",
        "team",
        "priority",
        "status",
        "progress",
        "is_archived",
        "created_at",
    )
    list_filter = ("status", "priority", "is_archived")
    search_fields = ("name", "description")


@admin.register(ProjectMember)
class ProjectMemberAdmin(admin.ModelAdmin):
    list_display = (
        "project",
        "user",
        "joined_at",
    )
    list_filter = ("project",)
    search_fields = (
        "project__name",
        "user__username",
        "user__email",
    )

@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "project",
        "status",
        "due_date",
        "created_at",
    )
    list_filter = ("status", "project")
    search_fields = (
        "name",
        "project__name",
    )