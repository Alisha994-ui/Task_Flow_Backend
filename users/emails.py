"""
Account e-mails: welcome (new account) and password reset by an admin.

Both contain the username and the password the admin set, as requested.
Sending never raises - a mail-server problem must not roll back the account
change - it returns False instead, so the API can tell the admin.
"""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape

logger = logging.getLogger(__name__)


def _app_name():
    return getattr(settings, "TASKFLOW_APP_NAME", "TaskFlow")


def _display_name(user):
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.username


def _send(user, subject, intro_text, intro_html, raw_password):
    if not user.email:
        logger.warning("Account e-mail skipped: user %s has no e-mail.", user.pk)
        return False

    app = _app_name()
    name = _display_name(user)

    text = (
        f"Hello {name},\n\n"
        f"{intro_text}\n\n"
        f"Username: {user.username}\n"
        f"Password: {raw_password}\n\n"
        f"Sign in to the {app} app with these details. The password is "
        f"case-sensitive. For your security, do not share this e-mail and "
        f"ask your administrator to change the password if you think "
        f"someone else has seen it.\n\n"
        f"Regards,\n{app}"
    )

    html = f"""
<div style="font-family:Arial,Helvetica,sans-serif;font-size:14px;color:#1f2937;max-width:520px">
  <p>Hello {escape(name)},</p>
  <p>{intro_html}</p>
  <table cellpadding="8" style="border-collapse:collapse;border:1px solid #e5e7eb;margin:12px 0">
    <tr><td style="background:#f9fafb;border:1px solid #e5e7eb"><b>Username</b></td>
        <td style="border:1px solid #e5e7eb;font-family:monospace">{escape(user.username)}</td></tr>
    <tr><td style="background:#f9fafb;border:1px solid #e5e7eb"><b>Password</b></td>
        <td style="border:1px solid #e5e7eb;font-family:monospace">{escape(raw_password)}</td></tr>
  </table>
  <p>Sign in to the {escape(app)} app with these details. The password is case-sensitive.</p>
  <p style="color:#6b7280;font-size:12px">For your security, do not share this e-mail. Ask your
  administrator to change the password if you think someone else has seen it.</p>
  <p>Regards,<br>{escape(app)}</p>
</div>
""".strip()

    try:
        message = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
            to=[user.email],
        )
        message.attach_alternative(html, "text/html")
        message.send(fail_silently=False)
        return True
    except Exception:  # noqa: BLE001 - any SMTP/backend failure
        logger.exception("Could not send account e-mail to user %s.", user.pk)
        return False


def send_welcome_email(user, raw_password):
    app = _app_name()
    return _send(
        user,
        subject=f"Your {app} account has been created",
        intro_text=f"An administrator has added you to {app}. Your sign-in details are:",
        intro_html=f"An administrator has added you to <b>{escape(app)}</b>. Your sign-in details are:",
        raw_password=raw_password,
    )


def send_password_reset_email(user, raw_password):
    app = _app_name()
    return _send(
        user,
        subject=f"Your {app} password has been reset",
        intro_text=f"An administrator has reset your {app} password. Your new sign-in details are:",
        intro_html=f"An administrator has reset your <b>{escape(app)}</b> password. Your new sign-in details are:",
        raw_password=raw_password,
    )
