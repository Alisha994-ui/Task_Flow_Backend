from django.conf import settings
from django.db import models

class Notification(models.Model):
    class Type(models.TextChoices):
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task Assigned"
        TASK_REASSIGNED = "TASK_REASSIGNED", "Task Reassigned"
        DEADLINE = "DEADLINE", "Deadline Reminder"
        OVERDUE = "OVERDUE", "Overdue"
        COMMENT = "COMMENT", "Comment"
        MENTION = "MENTION", "Mention"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    task = models.ForeignKey("tasks.Task", on_delete=models.CASCADE, null=True, blank=True, related_name="notifications")
    type = models.CharField(max_length=30, choices=Type.choices)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"