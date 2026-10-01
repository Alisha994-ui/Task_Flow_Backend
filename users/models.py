from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
        TEAM_LEAD = "TEAM_LEAD", "Team Lead"
        EMPLOYEE = "EMPLOYEE", "Employee"
        VIEWER = "VIEWER", "Viewer"

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.EMPLOYEE
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_image = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.username} - {self.role}"