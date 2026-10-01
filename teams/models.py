from django.conf import settings
from django.db import models


class Team(models.Model):

    name = models.CharField(max_length=100)

    description = models.TextField(
        blank=True,
        null=True
    )

    team_lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_teams"
    )

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="TeamMember",
        related_name="teams",
        blank=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TeamMember(models.Model):

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="team_members"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships"
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["team", "user"],
                name="unique_team_member"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"