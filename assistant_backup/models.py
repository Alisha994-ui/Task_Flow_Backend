from django.conf import settings
from django.db import models


class AssistantMessage(models.Model):
    """One turn of a person's conversation with the assistant.

    Kept so the thread survives closing the app, and so the last few
    turns can be sent back as context - without them the assistant
    cannot follow up on "and what about Ali?".
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assistant_messages",
    )
    role = models.CharField(max_length=10, choices=Role.choices)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user.username} ({self.role})"
