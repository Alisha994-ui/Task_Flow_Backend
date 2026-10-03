from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from notifications.models import Notification
from .models import Task, Subtask, Comment, Label, Attachment, ActivityLog, TimeLog
from .serializers import TaskSerializer, SubtaskSerializer, CommentSerializer, LabelSerializer, AttachmentSerializer, ActivityLogSerializer, TimeLogSerializer
from .permissions import TaskPermission, CommentPermission, AttachmentPermission, TimeLogPermission, ActivityLogPermission, SubtaskPermission, LabelPermission

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().order_by("-created_at")
    serializer_class = TaskSerializer
    permission_classes = [TaskPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all().order_by("-created_at")
        if user.role == "ADMIN":
            pass
        elif user.role == "PROJECT_MANAGER":
            queryset = queryset.filter(project__manager=user)
        elif user.role == "TEAM_LEAD":
            queryset = queryset.filter(project__team__team_lead=user)
        elif user.role == "EMPLOYEE":
            queryset = queryset.filter(assignee=user)
        elif user.role == "VIEWER":
            queryset = queryset.filter(project__project_members__user=user).distinct()
        else:
            return queryset.none()

        params = self.request.query_params
        if params.get("status"):
            queryset = queryset.filter(status=params.get("status"))
        if params.get("priority"):
            queryset = queryset.filter(priority=params.get("priority"))
        if params.get("project"):
            queryset = queryset.filter(project_id=params.get("project"))
        if params.get("assignee"):
            queryset = queryset.filter(assignee_id=params.get("assignee"))
        if params.get("search"):
            queryset = queryset.filter(title__icontains=params.get("search"))
        if params.get("overdue") == "true":
            queryset = queryset.filter(due_date__lt=timezone.now().date()).exclude(status=Task.Status.COMPLETED)
        return queryset

    def update_project_progress(self, project):
        total = project.tasks.count()
        completed = project.tasks.filter(status=Task.Status.COMPLETED).count()
        project.progress = round((completed / total) * 100) if total else 0
        project.save(update_fields=["progress"])

    def perform_create(self, serializer):
        task = serializer.save(creator=self.request.user)
        self.update_project_progress(task.project)
        ActivityLog.objects.create(task=task, user=self.request.user, action="TASK_CREATED", description=f'Task "{task.title}" was created.')
        if task.assignee:
            Notification.objects.create(user=task.assignee, task=task, type=Notification.Type.TASK_ASSIGNED, title="New Task Assigned", message=f'You have been assigned the task "{task.title}".')

    def perform_update(self, serializer):
        old_task = self.get_object()
        old_status = old_task.status
        old_assignee = old_task.assignee
        task = serializer.save()
        self.update_project_progress(task.project)

        if task.status != old_status:
            ActivityLog.objects.create(task=task, user=self.request.user, action="STATUS_CHANGED", description=f"Status changed from {old_status} to {task.status}.")

        if task.assignee != old_assignee:
            ActivityLog.objects.create(task=task, user=self.request.user, action="TASK_REASSIGNED", description=f'Task "{task.title}" was reassigned.')
            if task.assignee:
                Notification.objects.create(user=task.assignee, task=task, type=Notification.Type.TASK_REASSIGNED, title="Task Reassigned", message=f'You have been assigned the task "{task.title}".')

    @action(detail=False, methods=["get"], url_path="my")
    def my_tasks(self, request):
        tasks = Task.objects.filter(assignee=request.user).order_by("-created_at")
        return Response(TaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        tasks = Task.objects.filter(assignee=request.user)
        today = timezone.now().date()
        return Response({
            "total": tasks.count(),
            "pending": tasks.filter(status=Task.Status.TODO).count(),
            "in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            "completed": tasks.filter(status=Task.Status.COMPLETED).count(),
            "overdue": tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).count()
        })

    @action(detail=False, methods=["get"], url_path="calendar")
    def calendar(self, request):
        tasks = self.get_queryset()
        start = request.query_params.get("start")
        end = request.query_params.get("end")
        if start:
            tasks = tasks.filter(due_date__gte=start)
        if end:
            tasks = tasks.filter(due_date__lte=end)
        return Response(TaskSerializer(tasks, many=True).data)

    @action(detail=False, methods=["get"], url_path="manager-dashboard")
    def manager_dashboard(self, request):
        tasks = Task.objects.filter(project__manager=request.user)
        today = timezone.now().date()
        return Response({
            "total": tasks.count(),
            "pending": tasks.filter(status=Task.Status.TODO).count(),
            "in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            "completed": tasks.filter(status=Task.Status.COMPLETED).count(),
            "overdue": tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).count()
        })

    @action(detail=False, methods=["get"], url_path="team-lead-dashboard")
    def team_lead_dashboard(self, request):
        tasks = Task.objects.filter(project__team__team_lead=request.user)
        today = timezone.now().date()
        return Response({
            "total": tasks.count(),
            "pending": tasks.filter(status=Task.Status.TODO).count(),
            "in_progress": tasks.filter(status=Task.Status.IN_PROGRESS).count(),
            "completed": tasks.filter(status=Task.Status.COMPLETED).count(),
            "overdue": tasks.filter(due_date__lt=today).exclude(status=Task.Status.COMPLETED).count()
        })

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None):
        task = self.get_object()
        if task.assignee != request.user:
            return Response({"detail": "You can only update your assigned tasks."}, status=403)

        old_status = task.status
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
        self.update_project_progress(task.project)

        if old_status != status:
            ActivityLog.objects.create(task=task, user=request.user, action="STATUS_CHANGED", description=f"Status changed from {old_status} to {status}.")

        return Response(TaskSerializer(task).data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by("created_at")
    serializer_class = CommentSerializer
    permission_classes = [CommentPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Comment.objects.all().order_by("created_at")
        if user.role == "PROJECT_MANAGER":
            return Comment.objects.filter(task__project__manager=user).order_by("created_at")
        if user.role == "TEAM_LEAD":
            return Comment.objects.filter(task__project__team__team_lead=user).order_by("created_at")
        if user.role == "EMPLOYEE":
            return Comment.objects.filter(task__assignee=user).order_by("created_at")
        if user.role == "VIEWER":
            return Comment.objects.filter(task__project__project_members__user=user).distinct().order_by("created_at")
        return Comment.objects.none()

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        task = comment.task
        ActivityLog.objects.create(task=task, user=self.request.user, action="COMMENT_ADDED", description=f'{self.request.user.username} added a comment.')
        if task.assignee and task.assignee != self.request.user:
            Notification.objects.create(user=task.assignee, task=task, type=Notification.Type.COMMENT, title="New Comment", message=f'{self.request.user.username} commented on your task "{task.title}".')

class SubtaskViewSet(viewsets.ModelViewSet):
    queryset = Subtask.objects.all().order_by("-created_at")
    serializer_class = SubtaskSerializer
    permission_classes = [SubtaskPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Subtask.objects.all().order_by("-created_at")
        if user.role == "PROJECT_MANAGER":
            return Subtask.objects.filter(task__project__manager=user).order_by("-created_at")
        if user.role == "TEAM_LEAD":
            return Subtask.objects.filter(task__project__team__team_lead=user).order_by("-created_at")
        if user.role == "EMPLOYEE":
            return Subtask.objects.filter(task__assignee=user).order_by("-created_at")
        if user.role == "VIEWER":
            return Subtask.objects.filter(task__project__project_members__user=user).distinct().order_by("-created_at")
        return Subtask.objects.none()

class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all().order_by("name")
    serializer_class = LabelSerializer
    permission_classes = [LabelPermission]

class AttachmentViewSet(viewsets.ModelViewSet):
    queryset = Attachment.objects.all().order_by("-created_at")
    serializer_class = AttachmentSerializer
    permission_classes = [AttachmentPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return Attachment.objects.all().order_by("-created_at")
        if user.role == "PROJECT_MANAGER":
            return Attachment.objects.filter(task__project__manager=user).order_by("-created_at")
        if user.role == "TEAM_LEAD":
            return Attachment.objects.filter(task__project__team__team_lead=user).order_by("-created_at")
        if user.role == "EMPLOYEE":
            return Attachment.objects.filter(task__assignee=user).order_by("-created_at")
        if user.role == "VIEWER":
            return Attachment.objects.filter(task__project__project_members__user=user).distinct().order_by("-created_at")
        return Attachment.objects.none()

    def perform_create(self, serializer):
        attachment = serializer.save(uploaded_by=self.request.user)
        ActivityLog.objects.create(task=attachment.task, user=self.request.user, action="ATTACHMENT_ADDED", description=f'Attachment "{attachment.file.name}" was added.')

class ActivityLogViewSet(viewsets.ModelViewSet):
    queryset = ActivityLog.objects.all().order_by("-created_at")
    serializer_class = ActivityLogSerializer
    permission_classes = [ActivityLogPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role == "ADMIN":
            return ActivityLog.objects.all().order_by("-created_at")
        if user.role == "PROJECT_MANAGER":
            return ActivityLog.objects.filter(task__project__manager=user).order_by("-created_at")
        if user.role == "TEAM_LEAD":
            return ActivityLog.objects.filter(task__project__team__team_lead=user).order_by("-created_at")
        if user.role == "EMPLOYEE":
            return ActivityLog.objects.filter(task__assignee=user).order_by("-created_at")
        if user.role == "VIEWER":
            return ActivityLog.objects.filter(task__project__project_members__user=user).distinct().order_by("-created_at")
        return ActivityLog.objects.none()

class TimeLogViewSet(viewsets.ModelViewSet):
    queryset = TimeLog.objects.all().order_by("-start_time")
    serializer_class = TimeLogSerializer
    permission_classes = [TimeLogPermission]

    def get_queryset(self):
            user = self.request.user
            queryset = TimeLog.objects.all().order_by("-start_time")
    
            if user.role == "ADMIN":
                pass
            elif user.role == "PROJECT_MANAGER":
                queryset = queryset.filter(task__project__manager=user)
            elif user.role == "TEAM_LEAD":
                queryset = queryset.filter(task__project__team__team_lead=user)
            else:
                queryset = queryset.filter(user=user)
    
            params = self.request.query_params
            if params.get("task"):
                queryset = queryset.filter(task_id=params.get("task"))
            if params.get("user"):
                queryset = queryset.filter(user_id=params.get("user"))
    
            return queryset
    

    @action(detail=False, methods=["post"], url_path="start")
    def start_timer(self, request):
        task_id = request.data.get("task")
        if not task_id:
            return Response({"detail": "Task is required."}, status=400)

        active_timer = TimeLog.objects.filter(user=request.user, end_time__isnull=True).first()
        if active_timer:
            return Response({"detail": "You already have an active timer."}, status=400)

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found."}, status=404)

        time_log = TimeLog.objects.create(task=task, user=request.user, start_time=timezone.now())
        return Response(TimeLogSerializer(time_log).data, status=201)

    @action(detail=False, methods=["post"], url_path="stop")
    def stop_timer(self, request):
        time_log = TimeLog.objects.filter(user=request.user, end_time__isnull=True).first()
        if not time_log:
            return Response({"detail": "No active timer found."}, status=400)

        end_time = timezone.now()
        duration = int((end_time - time_log.start_time).total_seconds() / 60)
        time_log.end_time = end_time
        time_log.duration_minutes = duration
        time_log.save()

        ActivityLog.objects.create(task=time_log.task, user=request.user, action="TIME_LOGGED", description=f"Time tracked: {duration} minutes.")
        return Response(TimeLogSerializer(time_log).data)