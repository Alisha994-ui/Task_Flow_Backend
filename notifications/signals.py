"""Every new Notification becomes a push.

The tasks app already creates Notification rows for assignment,
reassignment and comments, so none of that code needs to change - this
listens to the model instead.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification
from .push import send_push_for_notification


@receiver(post_save, sender=Notification)
def push_on_notification(sender, instance, created, **kwargs):
    if not created:
        return

    send_push_for_notification(instance)
