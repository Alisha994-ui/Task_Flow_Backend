from rest_framework import serializers

from .models import ProjectMessage


class ProjectMessageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    user_full_name = serializers.SerializerMethodField()

    class Meta:
        model = ProjectMessage
        fields = (
            "id",
            "project",
            "user",
            "user_name",
            "user_full_name",
            "text",
            "file",
            "created_at",
        )
        read_only_fields = ("user", "created_at")

    def get_user_full_name(self, obj):
        full = f"{obj.user.first_name} {obj.user.last_name}".strip()

        return full or obj.user.username

    def validate(self, data):
        # A message with neither words nor a file is nothing at all.
        if not data.get("text") and not data.get("file"):
            raise serializers.ValidationError(
                {"text": "Write something or attach a file."}
            )

        return data
