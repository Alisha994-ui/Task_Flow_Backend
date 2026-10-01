from rest_framework import serializers
from .models import Team, TeamMember

class TeamMemberSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = TeamMember
        fields = ("id", "team", "user", "user_name", "joined_at")
        read_only_fields = ("joined_at",)

class TeamSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Team
        fields = "__all__"