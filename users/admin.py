from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin, ModelAdmin):
    list_display = ("username", "email", "role", "status", "is_active")
    list_filter = ("role", "status", "is_active")
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = UserAdmin.fieldsets + (
        (
            "TaskFlow Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "profile_image",
                    "status",
                )
            },
        ),
    )