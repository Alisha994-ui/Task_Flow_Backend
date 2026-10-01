from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Task
from .serializers import TaskSerializer
from rest_framework.response import Response
from .models import Task, Comment
from .serializers import TaskSerializer, CommentSerializer

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Task.objects.all().order_by("-created_at")
        params = self.request.query_params

        status = params.get("status")
        priority = params.get("priority")
        project = params.get("project")
        assignee = params.get("assignee")
        search = params.get("search")
        overdue = params.get("overdue")

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if project:
            queryset = queryset.filter(project_id=project)
        if assignee:
            queryset = queryset.filter(assignee_id=assignee)
        if search:
            queryset = queryset.filter(title__icontains=search)
        if overdue == "true":
            queryset = queryset.filter(due_date__lt=timezone.now().date()).exclude(status=Task.Status.COMPLETED)

        return queryset

    @action(detail=False, methods=["get"], url_path="my")
    def my_tasks(self, request):
        tasks = Task.objects.filter(assignee=request.user).order_by("-created_at")
        return Response(TaskSerializer(tasks, many=True).data)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        task = self.get_object()

        if task.assignee != request.user:
            return Response({"detail": "You can only update your assigned tasks."}, status=403)

        status = request.data.get("status")

        valid_statuses = [choice[0] for choice in Task.Status.choices]
        if status not in valid_statuses:
            return Response({"detail": "Invalid status."}, status=400)

        task.status = status

        if status == Task.Status.COMPLETED:
            task.progress = 100
        elif status == Task.Status.TODO:
            task.progress = 0

        task.save()
        return Response(TaskSerializer(task).data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by("created_at")
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

