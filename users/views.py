from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer

from django.utils import timezone
from projects.models import Project
from tasks.models import Task

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

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