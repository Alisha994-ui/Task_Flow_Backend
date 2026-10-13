from django.db.models import Q
from rest_framework import viewsets

from notifications.models import Notification

from .models import ProjectMessage
from .permissions import ProjectMessagePermission
from .serializers import ProjectMessageSerializer


class ProjectMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectMessageSerializer
    permission_classes = [ProjectMessagePermission]

    def get_queryset(self):
        user = self.request.user
        queryset = ProjectMessage.objects.select_related(
            "user", "project"
        ).all()

        # Same scoping the rest of the API uses, one level up: a person
        # sees the discussions of the projects they are part of.
        if user.role == "ADMIN":
            pass
        elif user.role == "PROJECT_MANAGER":
            queryset = queryset.filter(project__manager=user)
        elif user.role == "TEAM_LEAD":
            queryset = queryset.filter(project__team__team_lead=user)
        else:
            queryset = queryset.filter(
                Q(project__team__members=user)
                | Q(project__project_members__user=user)
                | Q(project__tasks__assignee=user)
            ).distinct()

        project = self.request.query_params.get("project")

        if project:
            queryset = queryset.filter(project_id=project)

        return queryset.order_by("created_at")

    def perform_create(self, serializer):
        message = serializer.save(user=self.request.user)

        self._notify_others(message)

    def _notify_others(self, message):
        """Tells the rest of the project, not the person who just wrote.

        A discussion message is not about one task, so the notification
        carries no task - tapping it opens the notifications list.
        """
        project = message.project
        author = message.user

        people = set()

        if project.manager:
            people.add(project.manager)

        if project.team:
            if project.team.team_lead:
                people.add(project.team.team_lead)

            people.update(project.team.members.all())

        people.update(
            member.user for member in project.project_members.all()
        )

        people.discard(author)
        people.discard(None)

        preview = message.text.strip()

        if not preview:
            preview = "shared a file"
        elif len(preview) > 80:
            preview = preview[:77] + "..."

        for person in people:
            Notification.objects.create(
                user=person,
                task=None,
                type=Notification.Type.COMMENT,
                title=f"{project.name}",
                message=f"{author.username}: {preview}",
            )
