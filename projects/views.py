from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Project, ProjectMember, Milestone
from .serializers import ProjectSerializer, ProjectMemberSerializer, MilestoneSerializer
from .permissions import ProjectPermission, ProjectMemberPermission, MilestonePermission

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by("-created_at")
    serializer_class = ProjectSerializer
    permission_classes = [ProjectPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Project.objects.all().order_by("-created_at")
        if user.role == "PROJECT_MANAGER":
            return Project.objects.filter(manager=user).order_by("-created_at")
        if user.role == "TEAM_LEAD":
            return Project.objects.filter(team__team_lead=user).order_by("-created_at")
        if user.role in ["EMPLOYEE", "VIEWER"]:
            return Project.objects.filter(project_members__user=user).distinct().order_by("-created_at")
        return Project.objects.none()

    @action(detail=True, methods=["get"], url_path="progress")
    def project_progress(self, request, pk=None):
        project = self.get_object()
        total = project.tasks.count()
        completed = project.tasks.filter(status="COMPLETED").count()
        progress = round((completed / total) * 100) if total else 0
        project.progress = progress
        project.save(update_fields=["progress"])
        return Response({
            "project": project.id,
            "total_tasks": total,
            "completed_tasks": completed,
            "progress": progress
        })

class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all().order_by("-joined_at")
    serializer_class = ProjectMemberSerializer
    permission_classes = [ProjectMemberPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return ProjectMember.objects.all().order_by("-joined_at")
        if user.role == "PROJECT_MANAGER":
            return ProjectMember.objects.filter(project__manager=user).order_by("-joined_at")
        if user.role == "TEAM_LEAD":
            return ProjectMember.objects.filter(project__team__team_lead=user).order_by("-joined_at")
        if user.role in ["EMPLOYEE", "VIEWER"]:
            return ProjectMember.objects.filter(user=user).order_by("-joined_at")
        return ProjectMember.objects.none()

class MilestoneViewSet(viewsets.ModelViewSet):
    queryset = Milestone.objects.all().order_by("due_date")
    serializer_class = MilestoneSerializer
    permission_classes = [MilestonePermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Milestone.objects.all().order_by("due_date")
        if user.role == "PROJECT_MANAGER":
            return Milestone.objects.filter(project__manager=user).order_by("due_date")
        if user.role == "TEAM_LEAD":
            return Milestone.objects.filter(project__team__team_lead=user).order_by("due_date")
        if user.role in ["EMPLOYEE", "VIEWER"]:
            return Milestone.objects.filter(project__project_members__user=user).distinct().order_by("due_date")
        return Milestone.objects.none()