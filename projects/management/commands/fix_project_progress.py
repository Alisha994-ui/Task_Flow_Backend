"""
One-time fix for BUG-06: existing projects whose progress/status were
already saved as inconsistent (e.g. 100% progress while still
"Planning") before the update_project_progress() fix went in.

This recomputes progress and applies the same status rule for every
project that already exists, so old rows get corrected immediately
instead of waiting for someone to touch one of their tasks.

WHERE TO PUT THIS FILE:
    <your_app>/management/commands/fix_project_progress.py

(<your_app> is whichever Django app has the Project model - likely
"projects". Django needs an empty __init__.py in both the
"management" and "management/commands" folders if they don't already
exist:
    projects/management/__init__.py
    projects/management/commands/__init__.py
)

HOW TO RUN:
    python manage.py fix_project_progress
"""

from django.core.management.base import BaseCommand

from projects.models import Project
from tasks.models import Task


class Command(BaseCommand):
    help = "Recompute progress and status consistency for every existing project (BUG-06 one-time fix)."

    def handle(self, *args, **options):
        changed = 0

        for project in Project.objects.all():
            total = project.tasks.count()
            completed = project.tasks.filter(status=Task.Status.COMPLETED).count()
            new_progress = round((completed / total) * 100) if total else 0

            old_progress = project.progress
            old_status = project.status

            project.progress = new_progress

            if project.status != Project.Status.CANCELLED:
                if project.progress == 100 and project.status != Project.Status.COMPLETED:
                    project.status = Project.Status.COMPLETED
                elif project.progress < 100 and project.status == Project.Status.COMPLETED:
                    project.status = Project.Status.ACTIVE

            if project.progress != old_progress or project.status != old_status:
                project.save(update_fields=["progress", "status"])
                changed += 1
                self.stdout.write(
                    f'"{project.name}": progress {old_progress}%->{project.progress}%, '
                    f"status {old_status}->{project.status}"
                )

        self.stdout.write(self.style.SUCCESS(f"Done. {changed} project(s) updated."))