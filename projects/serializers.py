from rest_framework import serializers
from .models import Project, ProjectMember, Milestone

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

class ProjectMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.username",
        read_only=True
    )

    class Meta:
        model = ProjectMember
        fields = (
            "id",
            "project",
            "user",
            "user_name",
            "joined_at",
        )
        read_only_fields = ("joined_at",)

class MilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Milestone
        fields = "__all__"