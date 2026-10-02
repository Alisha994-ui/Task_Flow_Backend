from rest_framework import serializers
from .models import Task, Subtask, Comment, Attachment, Label, ActivityLog, TimeLog

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

    def validate(self, data):
     start_date = data.get("start_date")
     due_date = data.get("due_date")
     progress = data.get("progress")

     if start_date and due_date and due_date < start_date:
        raise serializers.ValidationError({
            "due_date": "Due date cannot be before start date."
        })

     if progress is not None and not 0 <= progress <= 100:
        raise serializers.ValidationError({
            "progress": "Progress must be between 0 and 100."
        })

     return data

class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "user", "user_name", "text", "created_at", "updated_at")
        read_only_fields = ("user",)

class SubtaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subtask
        fields = "__all__"

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "user", "user_name", "text", "created_at", "updated_at")
        read_only_fields = ("user",)

class AttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source="uploaded_by.username", read_only=True)

    class Meta:
        model = Attachment
        fields = ("id", "task", "uploaded_by", "uploaded_by_name", "file", "created_at")
        read_only_fields = ("uploaded_by",)

class ActivityLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = ActivityLog
        fields = ("id", "task", "user", "user_name", "action", "description", "created_at")
        read_only_fields = ("user",)

class TimeLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TimeLog
        fields = ("id", "task", "user", "user_name", "start_time", "end_time", "duration_minutes", "note")
        read_only_fields = ("user",)

