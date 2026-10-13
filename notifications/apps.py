from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = 'notifications'

    def ready(self):
        # Importing the module connects the post_save signal that turns
        # every Notification row into a push. Without this line nothing
        # is ever sent.
        from . import signals  # noqa: F401
