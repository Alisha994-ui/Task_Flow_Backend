from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "manager", "team", "status", "priority", "progress", "is_archived")
    list_filter = ("status", "priority", "is_archived")
    search_fields = ("name", "description", "manager__username", "team__name")