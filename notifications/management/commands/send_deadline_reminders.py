"""Creates the DEADLINE and OVERDUE notifications.

These are the two Notification types nothing was writing yet. Run once
a day - the signal turns each row into a push automatically.

    python manage.py send_deadline_reminders

Options:
    --days 1     how far ahead counts as "due soon" (default 1)
    --dry-run    print what it would send, write nothing
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.models import Notification
from tasks.models import Task


class Command(BaseCommand):
    help = "Notify assignees about tasks due soon and tasks already overdue."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=1)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        days = options["days"]
        dry = options["dry_run"]

        today = timezone.now().date()
        horizon = today + timedelta(days=days)

        due_soon = Task.objects.filter(
            due_date__gte=today,
            due_date__lte=horizon,
            assignee__isnull=False,
        ).exclude(status=Task.Status.COMPLETED)

        overdue = Task.objects.filter(
            due_date__lt=today,
            assignee__isnull=False,
        ).exclude(status=Task.Status.COMPLETED)

        sent = 0

        for task in due_soon:
            if self._already_sent(task, Notification.Type.DEADLINE):
                continue

            when = "today" if task.due_date == today else "soon"

            if dry:
                self.stdout.write(f"DEADLINE  {task.assignee} - {task.title}")
            else:
                Notification.objects.create(
                    user=task.assignee,
                    task=task,
                    type=Notification.Type.DEADLINE,
                    title="Deadline approaching",
                    message=f'"{task.title}" is due {when}.',
                )

            sent += 1

        for task in overdue:
            if self._already_sent(task, Notification.Type.OVERDUE):
                continue

            late = (today - task.due_date).days

            if dry:
                self.stdout.write(f"OVERDUE   {task.assignee} - {task.title}")
            else:
                Notification.objects.create(
                    user=task.assignee,
                    task=task,
                    type=Notification.Type.OVERDUE,
                    title="Task is overdue",
                    message=(
                        f'"{task.title}" was due {late} '
                        f'{"day" if late == 1 else "days"} ago.'
                    ),
                )

            sent += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{'Would send' if dry else 'Sent'} {sent} reminder(s)."
            )
        )

    def _already_sent(self, task, kind):
        """Keeps the job idempotent - running it twice in a day does not
        notify the same person twice."""
        since = timezone.now() - timedelta(hours=20)

        return Notification.objects.filter(
            task=task,
            user=task.assignee,
            type=kind,
            created_at__gte=since,
        ).exists()
