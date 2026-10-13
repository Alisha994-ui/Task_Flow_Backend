import secrets
import string

from rest_framework import serializers

from .models import User

MIN_PASSWORD_LENGTH = 8


def generate_password(length=12):
    """Readable random password: letters + digits, no look-alikes."""
    alphabet = "".join(
        c for c in string.ascii_letters + string.digits if c not in "Il1O0o"
    )

    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))

        if any(c.isdigit() for c in password) and any(c.isalpha() for c in password):
            return password


def check_password_value(password):
    """
    Shared rules for every password an admin sets.

    Leading/trailing spaces are rejected rather than stored: a phone
    keyboard that appends a space after a suggestion would otherwise save
    a password the user can never type at sign-in (BUG-28).
    """
    if not password:
        raise serializers.ValidationError("Password cannot be empty.")

    if password != password.strip():
        raise serializers.ValidationError(
            "Password cannot start or end with a space."
        )

    if len(password) < MIN_PASSWORD_LENGTH:
        raise serializers.ValidationError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
        )

    return password


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False,
        trim_whitespace=False
    )

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
            "role",
            "phone",
            "profile_image",
            "status",
        )
        read_only_fields = ("id",)

    # ------------------------------------------------------------ fields

    def validate_username(self, value):
        value = (value or "").strip()

        if not value:
            raise serializers.ValidationError("Username is required.")

        if " " in value:
            raise serializers.ValidationError("Username cannot contain spaces.")

        # Sign-in is case-insensitive, so "Ali" and "ali" must not both exist.
        clash = User.objects.filter(username__iexact=value)

        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)

        if clash.exists():
            raise serializers.ValidationError(
                "A user with that username already exists."
            )

        return value

    def validate_email(self, value):
        value = (value or "").strip().lower()

        clash = User.objects.filter(email__iexact=value)

        if self.instance is not None:
            clash = clash.exclude(pk=self.instance.pk)

        if clash.exists():
            raise serializers.ValidationError(
                "A user with that email already exists."
            )

        return value

    def validate_password(self, value):
        return check_password_value(value)

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({
                "password": "Password is required when creating a user."
            })

        return attrs

    # ------------------------------------------------------------- save

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        # Keep Django's own flag in step with the app's Active switch, so a
        # switched-off account really cannot sign in.
        user.is_active = validated_data.get("status", True)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if "status" in validated_data:
            instance.is_active = validated_data["status"]

        if password is not None:
            instance.set_password(password)

        instance.save()
        return instance


class AdminPasswordResetSerializer(serializers.Serializer):
    """
    Body for POST /users/{id}/reset-password/.

    Leave `password` out (or empty) to have the server generate one.
    """

    password = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=False,
        write_only=True,
    )

    def validate_password(self, value):
        if value == "":
            return value

        return check_password_value(value)
