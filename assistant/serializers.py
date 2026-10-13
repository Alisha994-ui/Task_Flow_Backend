from rest_framework import serializers

from .models import AssistantMessage


class AssistantMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantMessage
        fields = ("id", "role", "text", "created_at")
        read_only_fields = fields
