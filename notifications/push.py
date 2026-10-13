"""Sends a Notification row out as a Firebase push.

Nothing in here raises. A push that fails must never break the request
that caused it - the in-app notification is already saved and the bell
will show it either way.
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_ready = False


def _ensure_firebase():
    """Starts firebase-admin once, the first time a push is needed."""
    global _firebase_ready

    if _firebase_ready:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        if not firebase_admin._apps:
            cred = credentials.Certificate(
                str(settings.FIREBASE_CREDENTIALS_FILE)
            )
            firebase_admin.initialize_app(cred)

        _firebase_ready = True

        return True
    except Exception as exc:
        logger.warning("Firebase not configured, no push sent: %s", exc)

        return False


def send_push_for_notification(notification):
    """Pushes one Notification to every device its owner has.

    task_id travels in the data block - that is what the app reads to
    open the right task when the person taps the notification.
    """
    if not _ensure_firebase():
        return

    from firebase_admin import messaging

    from .models import DeviceToken

    tokens = list(
        DeviceToken.objects.filter(user=notification.user)
        .values_list("token", flat=True)
    )

    if not tokens:
        return

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(
            title=notification.title,
            body=notification.message,
        ),
        data={
            "notification_id": str(notification.id),
            "task_id": str(notification.task_id or ""),
            "type": notification.type,
        },
        android=messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                channel_id="taskflow_default",
            ),
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(sound="default"),
            ),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
    except Exception as exc:
        logger.warning("Push send failed: %s", exc)

        return

    # Firebase reports which tokens are dead. Clearing them keeps the
    # table from filling up with uninstalled apps.
    dead = []

    for token, result in zip(tokens, response.responses):
        if result.success:
            continue

        code = getattr(result.exception, "code", "")

        if code in ("registration-token-not-registered", "invalid-argument"):
            dead.append(token)

    if dead:
        DeviceToken.objects.filter(token__in=dead).delete()
