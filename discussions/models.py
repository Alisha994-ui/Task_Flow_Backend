from django.conf import settings
from django.db import models


class ProjectMessage(models.Model):
    """A message in a project's discussion.

    Deliberately not a task comment: this is for the things that belong
    to the whole project - a client call tomorrow, a decision, a file
    everyone needs - which have nowhere sensible to live on a task.

    The file sits on the message itself rather than in a separate
    attachment table, because in a conversation a file is the message.
    """

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="project_messages",
    )
    text = models.TextField(blank=True)
    file = models.FileField(
        upload_to="discussion_files/",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} in {self.project.name}"
