from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models


class UserManager(DjangoUserManager):
    """
    Makes sign-in case-insensitive on the username.

    Django's ModelBackend (and therefore SimpleJWT's /auth/login/) looks the
    account up through get_by_natural_key(). By default that is an exact,
    case-sensitive match, so an account created as "Qa_Lead2" (phone
    keyboards like to capitalise the first letter) could never sign in as
    "qa_lead2". If two legacy rows differ only by case, fall back to the
    exact match instead of failing.
    """

    def get_by_natural_key(self, username):
        field = self.model.USERNAME_FIELD

        try:
            return self.get(**{f"{field}__iexact": username})
        except self.model.MultipleObjectsReturned:
            return self.get(**{field: username})


class User(AbstractUser):

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        PROJECT_MANAGER = "PROJECT_MANAGER", "Project Manager"
        TEAM_LEAD = "TEAM_LEAD", "Team Lead"
        EMPLOYEE = "EMPLOYEE", "Employee"

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

    objects = UserManager()

    def __str__(self):
        return f"{self.username} - {self.role}"
