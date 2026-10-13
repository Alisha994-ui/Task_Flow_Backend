from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import DeviceToken, Notification
from .serializers import DeviceTokenSerializer, NotificationSerializer


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


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """Where the app parks its Firebase token.

    A person only ever sees their own devices - there is nothing here
    worth exposing across users.
    """

    serializer_class = DeviceTokenSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        token = request.data.get("token")

        if not token:
            return Response({"detail": "Token is required."}, status=400)

        # The same phone can be handed to someone else, so the token
        # moves to whoever is signed in now rather than duplicating.
        device, _ = DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "platform": request.data.get("platform", "android"),
            },
        )

        return Response(
            DeviceTokenSerializer(device).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="remove")
    def remove(self, request):
        """Called on logout. Deletes by token, because the app never
        learns the row's id."""
        token = request.data.get("token")

        if not token:
            return Response({"detail": "Token is required."}, status=400)

        DeviceToken.objects.filter(token=token, user=request.user).delete()

        return Response({"message": "Device removed."})
