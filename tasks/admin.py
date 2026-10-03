from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Task, Subtask, Comment, Attachment, Label, ActivityLog, TimeLog
@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ("title", "project", "assignee", "priority", "status", "due_date", "progress")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "assignee__username", "project__name")

@admin.register(Subtask)
class SubtaskAdmin(ModelAdmin):
    list_display = ("title", "task", "is_done", "created_at")
    list_filter = ("is_done",)
    search_fields = ("title", "task__title")

@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("task", "user", "created_at")
    search_fields = ("text", "task__title", "user__username")

@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = ("task", "uploaded_by", "file", "created_at")
    search_fields = ("task__title", "uploaded_by__username")

@admin.register(Label)
class LabelAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(ActivityLog)
class ActivityLogAdmin(ModelAdmin):
    list_display = ("task", "user", "action", "created_at")
    list_filter = ("action",)
    search_fields = ("task__title", "user__username", "description")


@admin.register(TimeLog)
class TimeLogAdmin(ModelAdmin):
    list_display = ("task", "user", "start_time", "end_time", "duration_minutes")
    list_filter = ("user",)
    search_fields = ("task__title", "user__username", "note")