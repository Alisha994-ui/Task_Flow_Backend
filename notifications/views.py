from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).order_by("-created_at")

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications are created automatically."},
            status=403
        )

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications cannot be edited."},
            status=403
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use the read endpoint to update notification status."},
            status=403
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {"detail": "Notifications cannot be deleted."},
            status=403
        )

    @action(detail=True, methods=["patch"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])

        return Response(
            NotificationSerializer(notification).data
        )

    @action(detail=False, methods=["patch"], url_path="read-all")
    def mark_all_read(self, request):
        self.get_queryset().filter(
            is_read=False
        ).update(is_read=True)

        return Response({
            "message": "All notifications marked as read."
        })