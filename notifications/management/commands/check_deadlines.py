from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from tasks.models import Task
from notifications.models import Notification

class Command(BaseCommand):
    help = "Create deadline and overdue notifications"

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        tomorrow = today + timedelta(days=1)

        tasks = Task.objects.exclude(status=Task.Status.COMPLETED).filter(
            assignee__isnull=False
        )

        for task in tasks:
            if task.due_date == tomorrow:
                exists = Notification.objects.filter(
                    user=task.assignee,
                    task=task,
                    type=Notification.Type.DEADLINE,
                    created_at__date=today,
                ).exists()

                if not exists:
                    Notification.objects.create(
                        user=task.assignee,
                        task=task,
                        type=Notification.Type.DEADLINE,
                        title="Deadline Reminder",
                        message=f'Your task "{task.title}" is due tomorrow.',
                    )

            elif task.due_date and task.due_date < today:
                exists = Notification.objects.filter(
                    user=task.assignee,
                    task=task,
                    type=Notification.Type.OVERDUE,
                    created_at__date=today,
                ).exists()

                if not exists:
                    Notification.objects.create(
                        user=task.assignee,
                        task=task,
                        type=Notification.Type.OVERDUE,
                        title="Task Overdue",
                        message=f'Your task "{task.title}" is overdue.',
                    )

        self.stdout.write(
            self.style.SUCCESS("Deadline check completed.")
        )

