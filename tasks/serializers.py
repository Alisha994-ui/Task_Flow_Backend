from rest_framework import serializers
from .models import Task, Subtask, Comment, Attachment, Label, ActivityLog, TimeLog

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"

class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "task", "user", "user_name", "text", "created_at", "updated_at")
        read_only_fields = ("user",)