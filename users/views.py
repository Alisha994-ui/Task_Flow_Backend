from django.db import transaction
from django.utils import timezone
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from projects.models import Project
from tasks.models import Task

from .emails import send_password_reset_email, send_welcome_email
from .models import User
from .serializers import (
    AdminPasswordResetSerializer,
    UserSerializer,
    generate_password,
)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserManagementPermission(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True

        return request.user.role == User.Role.ADMIN


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [UserManagementPermission]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_password = serializer.validated_data["password"]

        with transaction.atomic():
            user = serializer.save()

        # Sent after the commit: the account exists even if mail fails.
        email_sent = send_welcome_email(user, raw_password)

        data = dict(serializer.data)
        data["email_sent"] = email_sent

        return Response(
            data,
            status=http_status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data),
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        raw_password = serializer.validated_data.get("password")

        with transaction.atomic():
            user = serializer.save()

        data = dict(serializer.data)

        if raw_password:
            data["email_sent"] = send_password_reset_email(user, raw_password)

        return Response(data)

    @action(detail=True, methods=["post"], url_path="reset-password")
    def reset_password(self, request, pk=None):
        """
        POST /api/users/{id}/reset-password/   (admin only)

        Body: {"password": "..."}  - or {} to let the server generate one.
        Sets the password, e-mails the username + new password to the user.
        """
        user = self.get_object()

        serializer = AdminPasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        password = serializer.validated_data.get("password") or ""
        generated = password == ""

        if generated:
            password = generate_password()

        user.set_password(password)
        user.save(update_fields=["password"])

        email_sent = send_password_reset_email(user, password)

        data = {
            "detail": (
                f"Password reset. The new details were e-mailed to {user.email}."
                if email_sent
                else "Password reset, but the e-mail could not be sent. "
                     "Share the new password with the user directly."
            ),
            "email_sent": email_sent,
        }

        # A generated password the user never received would lock them
        # out, so hand it to the admin only when the e-mail failed.
        if generated and not email_sent:
            data["password"] = password

        return Response(data, status=http_status.HTTP_200_OK)


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != User.Role.ADMIN:
            return Response({"detail": "Admin access required."}, status=403)

        today = timezone.now().date()

        return Response({
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(status=True).count(),
            "total_projects": Project.objects.count(),
            "total_tasks": Task.objects.count(),
            "completed_tasks": Task.objects.filter(
                status=Task.Status.COMPLETED
            ).count(),
            "pending_tasks": Task.objects.filter(
                status=Task.Status.TODO
            ).count(),
            "in_progress_tasks": Task.objects.filter(
                status=Task.Status.IN_PROGRESS
            ).count(),
            "overdue_tasks": Task.objects.filter(
                due_date__lt=today
            ).exclude(
                status=Task.Status.COMPLETED
            ).count(),
        })


class AppConfigView(APIView):
    permission_classes = []

    def get(self, request):
        admin_email = (
            User.objects
            .filter(role=User.Role.ADMIN, status=True)
            .values_list("email", flat=True)
            .first()
        )

        return Response({
            "support_email": admin_email or ""
        })
