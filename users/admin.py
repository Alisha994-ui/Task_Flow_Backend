from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from unfold.admin import ModelAdmin

from .emails import send_password_reset_email, send_welcome_email
from .models import User


class EmailingPasswordChangeForm(AdminPasswordChangeForm):
    """Django admin > user > "Reset password": also e-mails the user."""

    def save(self, commit=True):
        user = super().save(commit=commit)
        raw_password = self.cleaned_data.get("password1")

        # Empty when the admin chose "password-based authentication: disabled".
        self.email_sent = bool(commit and raw_password) and send_password_reset_email(
            user, raw_password
        )

        return user


@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    change_password_form = EmailingPasswordChangeForm

    list_display = (
        "username",
        "email",
        "role",
        "status",
        "is_active",
    )

    list_filter = (
        "role",
        "status",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
    )

    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "TaskFlow Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "profile_image",
                    "status",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "TaskFlow Information",
            {
                "fields": (
                    "email",
                    "role",
                    "phone",
                    "profile_image",
                    "status",
                ),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if obj.email:
            obj.email = obj.email.strip().lower()

        super().save_model(request, obj, form, change)

        if change:
            return

        raw_password = form.cleaned_data.get("password1")

        if not raw_password:
            return

        if send_welcome_email(obj, raw_password):
            self.message_user(request, f"Welcome e-mail sent to {obj.email}.")
        else:
            self.message_user(
                request,
                "Account created, but the welcome e-mail could not be sent. "
                "Check the e-mail settings.",
                level=messages.WARNING,
            )

    def user_change_password(self, request, id, form_url=""):
        response = super().user_change_password(request, id, form_url)

        # A redirect means the form was valid and the password was saved.
        if request.method == "POST" and response.status_code in (301, 302):
            self.message_user(
                request,
                "The user has been e-mailed their new password "
                "(check the server log if it does not arrive).",
            )

        return response
